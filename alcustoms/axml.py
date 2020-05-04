import io
import re
import xml.etree.ElementTree as ET


RE_ROOT=re.compile("<([^?]*)>")
RE_NAMESPACES=re.compile('xmlns:(\w*)="([^"]*)')
RE_NAMESPACEPARSE=re.compile('{(.*)}(.*)')

def parse(file):
    if isinstance(file,str):
        with open(file) as f:
            xmlstring=f.read()
        tree=ET.ElementTree(ET.fromstring(xmlstring),file=file)
    elif isinstance(file,io.IOBase):
        xmlstring=str(file.read(),encoding='utf-8')
        tree=ET.ElementTree(ET.fromstring(xmlstring))
    else:
        raise TypeError('File must be string path to file or File-Object')
    namespaces=get_namespaces(xmlstring)
    if namespaces:
        ET._namespace_map=dict()
        for uri,namespace in namespaces.items():
            ET.register_namespace(namespace,uri)
    return tree
    
def get_namespaces(xmlstring):
    root=RE_ROOT.findall(xmlstring)
    if not root:
        raise IOError('Malformed XML Doc')
    rawnamespaces=RE_NAMESPACES.findall(root[0])
    namespaces=dict((space,name) for name,space in rawnamespaces)
    return namespaces

def get_tag(tag,namespaces):
    namespace=RE_NAMESPACEPARSE.findall(tag)
    if not namespace:return tag
    namespace,tag=namespace[0]
    if not namespace in namespaces: return '{ns}:{tag}'.format(ns=namespace,tag=tag)
    return '{ns}:{tag}'.format(ns=namespaces[namespace],tag=tag)

def tabprint(*args,tab=0,**kw):
   print('{tab}{args}'.format(tab=tab*'\t',args=''.join(args)),**kw)
def prettyprintxml(xmlelement,namespaces={},tab=0):
##   print(tab*'\t'+str(ET.tostring(xmlelement)))
##   print(tab*'\t'+xmlelement.tag)
##   print(tab*'\t'+xmlelement.namespaces)
##   print(tab*'\t'+str(xmlelement.attrib))
##   print(tab*'\t'+xmlelement.tail)
   if not namespaces: namespaces=ET._namespace_map
   if isinstance(xmlelement,ET.ElementTree):\
      return prettyprintxml(xmlelement.getroot(),namespaces=namespaces,tab=tab)
   tag=get_tag(xmlelement.tag,namespaces)
   if xmlelement.attrib:
      attrib=' '+' '.join(
         '{}="{}"'.format(get_tag(key,namespaces),value) for key,value in xmlelement.attrib.items())
   else: attrib=''
   if tab==0:
      openelement='<{tag}{attrib}{namespace}>'.format(tag=tag,attrib=attrib,namespace=' '+' '.join('xmlns:{value}="{key}"'.format(value=value,key=key) for key,value in namespaces.items()))
   else:
      openelement='<{tag}{attrib}>'.format(tag=tag,attrib=attrib)
   endelement='</{tag}>'.format(tag=tag)
   if not xmlelement:
      if not xmlelement.text:
         endelement='<{tag}/>'.format(tag=tag)
         tabprint(endelement,tab=tab)
      else:
          tabprint('{openelement}{text}{endelement}'.format(openelement=openelement, text=xmlelement.text,endelement=endelement),tab=tab)
      return
   tabprint(openelement,tab=tab)
   if xmlelement.text:
       tabprint(xmlelement.text,tab=tab+1)
   for ele in xmlelement:
      prettyprintxml(ele,namespaces=namespaces,tab=tab+1)
   tabprint(endelement,tab=tab)
   if xmlelement.tail:
      tabprint(xmlelement.tail,tab=tab-1)
   return

if __name__=='__main__':
    def split():print('-'*10)
    print('parsing')
    tree=parse('tests/axmltest.xml')
    print('>>> done')
    split()
    print('getting root')
    root=tree.getroot()
    print('>>> done')
    split()
    print('tree')
    ET.dump(tree)
    split()
    print('pretty print')
    prettyprintxml(root)
    split()
    print('writing')
    tree.write('tests/axmltest2.xml')
    print('>>> done')
    split()
    print('loading written')
    tree=parse('tests/axmltest.xml')
    print('>>> done')
    split()
    print('getting new root')
    root=tree.getroot()
    print('>>> done')
    split()
    print('new tree')
    ET.dump(tree)
    split()
    print('new pretty print')
    prettyprintxml(root)
    split()
    print('done testing')
