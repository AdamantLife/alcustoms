""" A collection of table population utilities for testing """

## Sister Modules
from alcustoms.sql.objects import Connection,Table

## Builtin
import functools
import pathlib

TESTTABLESQL = """CREATE TABLE testtable(name TEXT, value INTEGER)"""
def gettesttableconstructor():
    return Table.TableConstructor("testtable",columns = dict(name="TEXT",value="INTEGER"))
def setupconnection(testcase):
    """ Creates a new database on testcase with 'testtable' table """
    testcase.connection = Connection.Database(file = ":memory:")
    testcase.connection.execute(TESTTABLESQL)

def populatetesttable(testcase):
    """ Sets what rows are in the testtable """
    testcase.connection.execute(""" DELETE FROM testtable;""")
    testcase.connection.execute(""" INSERT INTO testtable (name,value) VALUES ("Hello",1),("World",2);""")

TESTTABLESQL2 = """CREATE TABLE testtable2(forgnid INT REFERENCES testtable(rowid), myname TEXT);"""
TESTTABLESQL3 = """CREATE TABLE testtable3(myid INTEGER PRIMARY KEY, myvalue BOOLEAN);"""
TESTTABLESQL4 = """CREATE TABLE IF NOT EXISTS testtable4 (defaultvalue TEXT default "Hello World", uniquevalue BLOB UNIQUE, checkevenvalue INT CHECK(checkevenvalue % 2 = 0));"""
def setupadditionaltables(testcase):
    """ Adds additional tables for further testing """
    testcase.connection.execute(TESTTABLESQL2)
    testcase.connection.execute(TESTTABLESQL3)
    testcase.connection.execute(TESTTABLESQL4)
    testcase.testtables = [Table.Table(TESTTABLESQL),Table.Table(TESTTABLESQL2),Table.Table(TESTTABLESQL3),Table.Table(TESTTABLESQL4)]

def populatetesttable3(testcase):
    """ Sets what rows are in testtable3 """
    testcase.connection.execute(""" DELETE FROM testtable3;""")
    testcase.connection.execute(""" INSERT INTO testtable3 (myvalue) VALUES (1),(0),(0),(1);""")
def populatetesttable4(testcase):
    """ Sets what rows are in testtable4 """
    testcase.connection.execute(""" DELETE FROM testtable4;""")
    testcase.connection.execute(""" INSERT INTO testtable4 (uniquevalue, checkevenvalue) VALUES ("a",0),("b",2),("c",4),("d",6); """)

def populatealltables(testcase):
    """ Runs all available populatetesttable[x] commands """
    populatetesttable(testcase)
    populatetesttable3(testcase)
    populatetesttable4(testcase)

USERTABLESQL = """CREATE TABLE users (userid INTEGER PRIMARY KEY, fname TEXT, lname TEXT, email TEXT UNIQUE);"""
SECURITYTABLESQL = """CREATE TABLE notsecurity (userid INT REFERENCES users(userid) NOT NULL UNIQUE, salt BLOB NOT NULL, hash BLOB NOT NULL);"""
TOKENTABLESQL = """CREATE TABLE tokens (userid INT REFERENCES users(userid) NOT NULL UNIQUE ON CONFLICT REPLACE, token BLOB NOT NULL, issued TEXT NOT NULL);"""
POSTSTABLESQL = """CREATE TABLE posts (postid INTEGER PRIMARY KEY, userid INT REFERENCES users(userid) NOT NULL, posttime TEXT NOT NULL, post BLOB NOT NULL, tags BLOB);"""
COMMENTSTABLESQL = """CREATE TABLE comments (commentid INTEGER PRIMARY KEY, uid INT REFERENCES users(userid), pid INT REFERENCES posts(postid), commenttime TEXT NOT NULL, replyto INT REFERENCES comments(commentid), comment NOT NULL);"""

ADVANCEDROWS = [
    ["users",[
        dict(fname = "John", lname = "Doe", email = "jdoe2@email.internet"),dict(fname = "Jane", lname = "Doe", email = "jdoe@email.internet"),dict(fname = "Alice", lname = "Bob", email = "aliceisbestice@fraud.email"),dict(fname = "Carol", lname = "David", email = "crazycarol@altacct.com"),]
     ],
     ["notsecurity",[
         dict(userid=1,salt=1234,hash="ABCDEF"),dict(userid=2,salt=1234,hash="GHIJKL"),dict(userid=3,salt=1234,hash="MNOPQR"),dict(userid=4,salt=1234,hash="STUVWX"),]
      ],
      ["tokens",[
          dict(userid = 1, token = "alpha", issued = "19871208T0000+0000"),dict(userid = 2, token = "beta", issued = "17760704T1200-0500"),dict(userid = 3, token = "moe", issued = "19000726T0000+0600"),dict(userid = 4, token = "greyfacenospace", issued = "20110606T1337-0800"),]
       ],
       ["posts",[
           dict(userid=1, posttime = "20160101T0000+0000", post="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin vitae ullamcorper arcu.", tags = "blog daily life"),dict(userid=1, posttime = "20160102T0000+0000", post="Ut euismod, velit quis accumsan pharetra, nulla libero tempus eros, nec pellentesque orci dolor ut nulla. Integer pretium quam eu leo tempus consequat.", tags = "blog daily life"),
           dict(userid=3, posttime = "20160430T2245+0600", post="Ur Waifu is Trash.\n\nRead Here: bee5.biz/s1k3", tags = "alice amazing anime best bestgril camgirls celebrity cg cheats codes download exploit fake free gltch google guns hacks hollywood illuminati lifehack list lizardpeople money motorcycles nudes online photo playstation porn prank ranking real save tanks tape topten trucks video vines win waifu xbox xtreme xxx youtube"),dict(userid=3, posttime = "20160430T2300+0600", post="Why Flat is Justice: A Treatise\n\nRead Here: bee5.biz/3d551", tags = "alice amazing anime best bestgril camgirls celebrity cg cheats codes download exploit fake free gltch google guns hacks hollywood illuminati lifehack list lizardpeople money motorcycles nudes online photo playstation porn prank ranking real save tanks tape topten trucks video vines win waifu xbox xtreme xxx youtube"),dict(userid=3, posttime = "20160430T2315+0600", post="Abandon Your Tropey Cardboard Fanservice Waifus and Join the Cult of Alice\n\nRead Here: bee5.biz/ef5a6fe", tags = "alice amazing anime best bestgril camgirls celebrity cg cheats codes download exploit fake free gltch google guns hacks hollywood illuminati lifehack list lizardpeople money motorcycles nudes online photo playstation porn prank ranking real save tanks tape topten trucks video vines win waifu xbox xtreme xxx youtube"),
           dict(userid=1, posttime = "20160610T0500+0000", post="Praesent vehicula nibh sed pulvinar aliquet. In et massa ut metus laoreet placerat. Praesent sollicitudin, massa eget laoreet tempor, ligula enim blandit augue, eget convallis nibh elit viverra velit. Morbi vel lectus turpis.", tags = "blog life"),
           dict(userid=1, posttime = "20170101T0010+0000", post="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin vitae ullamcorper arcu.", tags = "blog stuff"),]
        ],
        ["comments",[
            dict(uid = 1, pid = 1, commenttime = "20160101T0001+0000", replyto = None, comment = "Thanks for reading, Everyone! It's my New Year's Resolution to write a post a day! Look forward to it!"),dict(uid = 1, pid = 2, commenttime = "20160102T0001+0000", replyto = None, comment = """Second post is up! Wasn't really sure what to write today, so I just kinda did a "Stream of Consciousness" thing: I hope that you all like it! Thanks again!"""),
            dict(uid = 1, pid = 3, commenttime = "20160430T1646+0000", replyto = None, comment = "Oh! Hi! Welcome to the forums! I don't really understand alot of what you said in your post, but I'm glad to see how passionate you are about it :) Hope you keep posting"),dict(uid = 1, pid = 4, commenttime = "20160430T1701+0000", replyto = None, comment = "Wow, you're really on a roll! I like your writing style :) It's very unique!"),dict(uid = 1, pid = 5, commenttime = "20160430T1716+0000", replyto = None, comment = "Y'know, I've been thinking for a while that I need to get back to my blog posts :-/... And you're inspiring me to do it :D\nDo you think you could give me some feedback on my posts? I think that would really help me figure out what I want to write about ^_^ <3"),
            dict(uid = 1, pid = 6, commenttime = "20160610T0500+0000", replyto = None, comment = "And I'm back! :D I know a lot of you were probably disappointed that I wasn't keeping up with the blog >.< But, you know, stuff was happening irl and I just kinda got lost in it all. Anywho! Hope you all enjoy my post! Be sure to comment! :D"),
            dict(uid = 4, pid = 1, commenttime = "20160609T2105-0800", replyto = None, comment = "lol"),dict(uid = 4, pid = 2, commenttime = "20160609T2105-0800", replyto = None, comment = "lol"),dict(uid = 4, pid = 3, commenttime = "20160609T2105-0800", replyto = None, comment = "lol"),dict(uid = 4, pid = 4, commenttime = "20160609T2105-0800", replyto = None, comment = "lol"),dict(uid = 4, pid = 5, commenttime = "20160609T2105-0800", replyto = None, comment = "lol"),dict(uid = 4, pid = 6, commenttime = "20160609T2105-0800", replyto = None, comment = "lol"),
            dict(uid = 1, pid = 6, commenttime = "20160610T0506+0000", replyto = 12, comment = "XD Glad you enjoyed it!"),dict(uid = 4, pid = 6, commenttime = "20160609T2106-0800", replyto = 13, comment = "lol"),dict(uid = 1, pid = 6, commenttime = "20160610T0506+0000", replyto = 14, comment = "???"),dict(uid = 4, pid = 6, commenttime = "20160609T2106-0800", replyto = 15, comment = "lol"),dict(uid = 1, pid = 6, commenttime = "20160610T0507+0000", replyto = 16, comment = "... I don't get it..."),dict(uid = 4, pid = 6, commenttime = "20160609T2107-0800", replyto = 17, comment = "lol"),
            dict(uid = 3, pid = 3, commenttime = "20160610T1330+0600", replyto = 7, comment = "Wtf"),dict(uid = 4, pid = 3, commenttime = "20160609T2331-0800", replyto = 19, comment = "lol"),dict(uid = 3, pid = 3, commenttime = "20160610T1331+0600", replyto = 20, comment = "No 1 carse trollfag"),dict(uid = 4, pid = 3, commenttime = "20160609T2331-0800", replyto = 21, comment = "lol"),dict(uid = 3, pid = 3, commenttime = "20160610T1331+0600", replyto = 22, comment = "So @#$%in original @#$%wad"),dict(uid = 4, pid = 3, commenttime = "20160609T2331-0800", replyto = 23, comment = "lol"),dict(uid = 3, pid = 3, commenttime = "20160610T1332+0600", replyto = 24, comment = "Where are the !@$%ing mods!? Sum1 ban this troll ffs!!!!"),dict(uid = 4, pid = 3, commenttime = "20160609T2332-0800", replyto = 25, comment = "lol"),dict(uid = 3, pid = 3, commenttime = "20160610T1332+0600", replyto = 26, comment = "This forum iz 2 trash 5 me. L8r Fags."),dict(uid = 4, pid = 3, commenttime = "20160609T2332-0800", replyto = 27, comment = "lol"),
            dict(uid = 1, pid = 7, commenttime = "20170101T0800+0000", replyto = None, comment = "Hey.\nI think I said most of the stuff I wanted to in the blog post. Like I said, I started this out hoping to talk to other people about stuff but...\nWell, I mean, I guess I was just a little bit over-optimistic. Recently it seems like nothing really goes as well as I hope.")
            ]]
    ]

def setupadvancedtables(testcase):
    """ Sets up a database Connection, Tables, and Rows in a "realistic" (heavy emphasis on the quotation marks) pattern for testing normal-use cases """
    for _sql in [USERTABLESQL,SECURITYTABLESQL,TOKENTABLESQL,POSTSTABLESQL,COMMENTSTABLESQL]: testcase.connection.execute(_sql)
    for table,rows in ADVANCEDROWS:
        tab = testcase.connection.getadvancedtable(table)
        setattr(testcase,table,tab)
        tab.addmultiple(*rows, grouping = False)    

TESTTABLESQL5 = """CREATE TABLE testtable5(checkvalue TEXT PRIMARY KEY CHECK (checkvalue IS NOT NULL), replacingvalue INTEGER UNIQUE ON CONFLICT REPLACE) WITHOUT ROWID;"""

class FactoryTestObject():
    def __init__(self,*args,**kwargs):
        self.args = args
        self.kwargs = kwargs

class RandomRowFactory():
    def __init__(self,cursor,row):
        self.cursor = cursor
        self.row = row

class TestObject():
    """ An object for testing AdvancedTable compatibility """
    def __init__(self, name = None, value = None, forgnid = None, rowid = None):
        self.name = name
        self.value = value
        self.forgnid = forgnid
        self.rowid = rowid
    def __eq__(self, other):
        if isinstance(other,TestObject):
            return all(getattr(self,k) == getattr(other,k) for k in ["name","value","forgnid","rowid"])

TESTVIEWSQL = """CREATE VIEW testview AS
SELECT name
FROM testtable
ORDER BY name;"""

def check_physicalfile():
    file = "__test__.db"
    file = pathlib.Path(file).resolve()
    if file.exists():
        try:
            file.unlink()
        except:
            time.sleep(1)
            file.unlink()
    return file

def filemanager(func):
    """ A Decorator to automatically check for, supply, and remove afterwards a physical file (per check_physicalfile) """
    @functools.wraps(func)
    def inner(*args,**kw):
        file = check_physicalfile()
        try: return func(*args,file = file, **kw)
        finally:
            ## check_physicalfile unlinks existing files
            ## and does not create a new (only returns a Path)
            check_physicalfile()
    return inner