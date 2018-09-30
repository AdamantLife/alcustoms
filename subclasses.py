import collections

class SumDict(collections.defaultdict):
    def __init__(self,*args,  default_factory=int, **dict):
        return super().__init__(default_factory, *args, **dict)
    def __add__(self,other):
        if not isinstance(other,dict):
            raise AttributeError("SumDict can only Sum Dictionaries")
        out=SumDict()
        out+=self
        out+=other
        return out
    def __iadd__(self,other):
        if not isinstance(other,dict):
            raise AttributeError("SumDict can only Sum Dictionaries")
        for key,value in other.items():
            self[key]+=value
        return self
    def sum(self,other):
        try:
            for otherdict in other:
                self+=otherdict
        except TypeError:
            raise TypeError("SumDict.sum takes an iterable")

class IndexDict(collections.OrderedDict):
    """ An Ordered Dict that can be accessed by index or key.

    Note that this means that IndexDict cannot store integers as key values:
    integers will be converted to strings first
    """
    def __getitem__(self,key):
        if isinstance(key,int):
            return super().__getitem__(list(self.keys())[key])
        elif isinstance(key,slice):
            return [super(self.__class__,self).__getitem__(k) for k in list(self.keys())[key]]
        else:
            return super().__getitem__(key)
    def __setitem__(self,key,value):
        if isinstance(key,int):
            key = str(key)
        super().__setitem__(key,value)

class pairdict(dict):
    """ A special dict that allows for lookup by-value as well as key.

        This imposes the following limitations:
            All values must also be immutable objects (as they cannot
                be set as reverse-keys otherwise)
            Keys that already exist in the dict cannot be set as values.
            Values that already exist in the dict cannot be set as keys.

        Existing keys can be assigned new values as normal, and new keys
        can be assigned to existing values. In the event that an
        existing key is assigned an existing value (or vise-versa),
        the orphaned, existing value and key (respectively) are dropped
        from the dict.

        Example usages:
            mydict = pairdict(a = "b")
            mydict["a"]
            >>> "b"
            mydict["b"]
            >>> "a"
            mydict[1] = 2
            mydict
            >>> {"a":"b", 1:2 }
            mydict["Hello World"] = [1,2,3]
            >>> ValueError[...]
            mydict[3] = 1
            mydict
            >>> {"a":"b", 1:3}
            mydict[1] = "a"
            >>> ValueError[...]
            mydict[1] = "b"
            mydict
            >>> {1:"b"}
    """
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw)
        self._reverse = dict((v,k) for k,v in self.items())
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            try:
                return self._reverse[key]
            except KeyError:
                raise KeyError(f"KeyError: {key}")
    def __setitem__(self, key, value):
        ## Remove previous key (__del__ will also remove pairing from _reverse)
        if key not in self:
            ## If setting via value: reorder for clarity, then remove value's previous key
            if key in self._reverse:
                value,key = key,value
                oldkey = self._reverse[value]
                del self[oldkey]

        ## Setting-Reference (whether key or value) should now have it's pair removed

        ## Now we check the Value-Reference (which may be key or value now)
        ## This will occur in collisions
        if key in self:
            del self[key]
        if value in self._reverse:
            oldkey = self._reverse[value]
            del self[oldkey]

        if value in self:
            raise ValueError("Key's value already exists as a Key")
        elif key in self._reverse:
            raise ValueError("Value's key already exists as a Value")
        try:
            super().__setitem__(key,value)
        except KeyError:
            raise KeyError("unhashable type: '{key.__class__.__name__}'")
        try:
            self._reverse[value] = key
        except KeyError:
            raise KeyError("unhashable type: '{value.__class__.__name__}'")
    def __delitem__(self, key):
        value = NotImplemented
        if key not in self:
            if key in self._reverse:
                value = key
                key = self._reverse[key]
        else:
            value = self[key]
        del self._reverse[value]
        return super().__delitem__(key)


"""
BELOW WAS STOLEN OFF OF INTERNET AND IS HERE FOR NOW

https://github.com/minillinim/stackedBarGraph

Demo was removed and is available at source
"""


###############################################################################
#                                                                             #
#    stackedBarGraph.py - code for creating purdy stacked bar graphs          #
#                                                                             #
###############################################################################
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program. If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

__author__ = "Michael Imelfort"
__copyright__ = "Copyright 2014"
__credits__ = ["Michael Imelfort"]
__license__ = "GPL3"
__version__ = "0.0.1"
__maintainer__ = "Michael Imelfort"
__email__ = "mike@mikeimelfort.com"
__status__ = "Development"

###############################################################################

import numpy as np
from matplotlib import pyplot as plt

###############################################################################

class StackedBarGrapher:
    """Container class"""
    def __init__(self): pass

    def stackedBarPlot(self,
                       ax,                                 # axes to plot onto
                       data,                               # data to plot
                       cols,                               # colors for each level
                       xLabels = None,                     # bar specific labels
                       yTicks = 6.,                        # information used for making y ticks ["none", <int> or [[tick_pos1, tick_pos2, ... ],[tick_label_1, tick_label2, ...]]
                       edgeCols=None,                      # colors for edges
                       showFirst=-1,                       # only plot the first <showFirst> bars
                       scale=False,                        # scale bars to same height
                       widths=None,                        # set widths for each bar
                       heights=None,                       # set heights for each bar
                       ylabel='',                          # label for x axis
                       xlabel='',                          # label for y axis
                       gap=0.,                             # gap between bars
                       endGaps=False                       # allow gaps at end of bar chart (only used if gaps != 0.)
                       ):

#------------------------------------------------------------------------------
# data fixeratering

        # make sure this makes sense
        if showFirst != -1:
            showFirst = np.min([showFirst, np.shape(data)[0]])
            data_copy = np.copy(data[:showFirst]).transpose().astype('float')
            data_shape = np.shape(data_copy)
            if heights is not None:
                heights = heights[:showFirst]
            if widths is not None:
                widths = widths[:showFirst]
            showFirst = -1
        else:
            data_copy = np.copy(data).transpose()
        data_shape = np.shape(data_copy)

        # determine the number of bars and corresponding levels from the shape of the data
        num_bars = data_shape[1]
        levels = data_shape[0]

        if widths is None:
            widths = np.array([1] * num_bars)
            x = np.arange(num_bars)
        else:
            x = [0]
            for i in range(1, len(widths)):
                x.append(x[i-1] + (widths[i-1] + widths[i])/2)

        # stack the data --
        # replace the value in each level by the cumulative sum of all preceding levels
        data_stack = np.reshape([float(i) for i in np.ravel(np.cumsum(data_copy, axis=0))], data_shape)

        # scale the data is needed
        if scale:
            data_copy /= data_stack[levels-1]
            data_stack /= data_stack[levels-1]
            if heights is not None:
                print("WARNING: setting scale and heights does not make sense.")
                heights = None
        elif heights is not None:
            data_copy /= data_stack[levels-1]
            data_stack /= data_stack[levels-1]
            for i in np.arange(num_bars):
                data_copy[:,i] *= heights[i]
                data_stack[:,i] *= heights[i]

#------------------------------------------------------------------------------
# ticks

        if yTicks is not "none":
            # it is either a set of ticks or the number of auto ticks to make
            real_ticks = True
            try:
                k = len(yTicks[1])
            except:
                real_ticks = False

            if not real_ticks:
                yTicks = float(yTicks)
                if scale:
                    # make the ticks line up to 100 %
                    y_ticks_at = np.arange(yTicks)/(yTicks-1)
                    y_tick_labels = np.array(["%0.2f"%(i * 100) for i in y_ticks_at])
                else:
                    # space the ticks along the y axis
                    y_ticks_at = np.arange(yTicks)/(yTicks-1)*np.max(data_stack)
                    y_tick_labels = np.array([str(i) for i in y_ticks_at])
                yTicks=(y_ticks_at, y_tick_labels)

#------------------------------------------------------------------------------
# plot

        if edgeCols is None:
            edgeCols = ["none"]*len(cols)

        # take cae of gaps
        gapd_widths = [i - gap for i in widths]

        # bars
        ax.bar(x,
               data_stack[0],
               color=cols[0],
               edgecolor=edgeCols[0],
               width=gapd_widths,
               linewidth=0.5,
               align='center'
               )

        for i in np.arange(1,levels):
            ax.bar(x,
                   data_copy[i],
                   bottom=data_stack[i-1],
                   color=cols[i],
                   edgecolor=edgeCols[i],
                   width=gapd_widths,
                   linewidth=0.5,
                   align='center'
                   )

        # borders
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)

        # make ticks if necessary
        if yTicks is not "none":
            ax.tick_params(axis='y', which='both', labelsize=8, direction="out")
            ax.yaxis.tick_left()
            plt.yticks(yTicks[0], yTicks[1])
        else:
            plt.yticks([], [])

        if xLabels is not None:
            ax.tick_params(axis='x', which='both', labelsize=8, direction="out")
            ax.xaxis.tick_bottom()
            plt.xticks(x, xLabels, rotation='vertical')
        else:
            plt.xticks([], [])

        # limits
        if endGaps:
            ax.set_xlim(-1.*widths[0]/2. - gap/2., np.sum(widths)-widths[0]/2. + gap/2.)
        else:
            ax.set_xlim(-1.*widths[0]/2. + gap/2., np.sum(widths)-widths[0]/2. - gap/2.)
        ax.set_ylim(0, yTicks[0][-1])#np.max(data_stack))

        # labels
        if xlabel != '':
            plt.xlabel(xlabel)
        if ylabel != '':
            plt.ylabel(ylabel)


###############################################################################
###############################################################################
###############################################################################
###############################################################################

if __name__ == '__main__':

    SBG = StackedBarGrapher()
    SBG.demo()

###############################################################################
###############################################################################
###############################################################################
###############################################################################
