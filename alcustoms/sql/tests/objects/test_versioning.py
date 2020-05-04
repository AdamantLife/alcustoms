import pathlib
import unittest
from alcustoms.sql import Database, Table, generate_dropcolumn
from alcustoms.sql.objects.versioning import *

class BasicCase(unittest.TestCase):
    def setUp(self):
        self.memdb = VersionedDatabase(":memory:")
        return super().setUp()

    def test_missing(self):
        """ Tests that Databases without a _versions table automatically create one. """
        self.assertEqual(len(self.memdb.getalltables()),1)
        self.assertTrue(self.memdb.tableexists(VERSIONTABLE))

        f = pathlib.Path("_______temp________.sqlite3test").resolve()
        f.touch()
        db = Database(f)
        try:
            db.execute("""CREATE TABLE blah(a);""")
            db.close()
        except Exception as e:
            db.close()
            f.unlink()
            raise e
        else:
            db.close()
        db = VersionedDatabase(f)
        try:
            self.assertTrue(db.tableexists(VERSIONTABLE))
            self.assertEqual(len(db.getalltables()),2)
        finally:
            db.close()
            f.unlink()

    def test_getversion(self):
        """ Tests the getversion function """
        self.memdb.execute("""CREATE TABLE blah(a);""")
        self.memdb.execute(f"""INSERT INTO {VERSIONTABLE} (tablename,version) VALUES ("blah","1.0");""")
        self.assertEqual(self.memdb.getversion("blah"),"1.0")
        self.memdb.execute(f"""UPDATE {VERSIONTABLE} SET version = "2.0" WHERE tablename = "blah";""")
        table = self.memdb.getadvancedtable("blah")
        self.assertEqual(self.memdb.getversion(table),"2.0")

    def test_updateversion_basic(self):
        """ Tests the updateversion function can add a version"""
        self.memdb.execute("""CREATE TABLE blah(a);""")
            
        self.memdb.updateversion("blah","1.0")
        self.assertEqual(self.memdb.getversion("blah"),"1.0")

        table = self.memdb.getadvancedtable("blah")
        self.memdb.updateversion(table,"2.0")
        self.assertEqual(self.memdb.getversion(table),"2.0")

    def test_updateversion_default_version(self):
        """ Tests that when no version is provided, the default is added instead """
        table = Table("""CREATE TABLE blah(a);""")
        self.memdb.addtables(table)
        self.memdb.updateversion(table)
        self.assertEqual(self.memdb.getversion(table),"2.0")
        self.memdb.default_version = "0.1"
        self.memdb.updateversion(table)
        self.assertEqual(self.memdb.getversion(table),"2.1")

    def test_addtable_hook(self):
        """ Tests that Database.addtable is properly extended """
        table = Table("""CREATE TABLE blah(a);""")
        success,fail = self.memdb.addtables(table)
        self.assertEqual(len(success),1)
        self.assertEqual(len(fail),0)
        self.assertEqual(self.memdb.getversion(table),"1.0")

        version = "12.34"
        self.memdb.default_version = version
        table = Table("""CREATE TABLE foo(b);""")
        self.memdb.addtables(table)
        self.assertEqual(self.memdb.getversion(table),version)

    def test_updateversion_updatescripts(self):
        """ Tests that the database applies the update script and stores the update/rollbackscripts if they are supplied """
        table = Table("""CREATE TABLE blah(a);""")
        self.memdb.addtables(table)

        version,updatescript,rollbackscript = "2.0","""ALTER TABLE blah ADD COLUMN b TEXT;""",generate_dropcolumn(table,"b")
        self.memdb.updateversion(table,version,updatescript,rollbackscript)

        with temp_row_factory(self.memdb,advancedrow_factory):
            versiontable = self.memdb.getadvancedtable(VERSIONTABLE)
            stats = versiontable.quickselect(tablename=table.name, version = version).first()
        self.assertEqual([stats.tablename.name,stats.version,stats.updatescript,stats.rollbackscript], [table.name,version,updatescript,rollbackscript])

        table = self.memdb.getadvancedtable("blah")
        self.assertEqual(len(table.columns),2)
        self.assertIn('b',table.columns)

    def test_rollback(self):
        """ Tests that the database can use rollbackscript to rollback a table """
        table = Table("""CREATE TABLE blah(a);""")
        self.memdb.addtables(table)
        self.memdb.updateversion(table,"2.0","""ALTER TABLE blah ADD COLUMN b TEXT;""",generate_dropcolumn(table,"b"))

        table = self.memdb.getadvancedtable("blah")
        self.assertIn("b",table.columns)

        self.memdb.rollbackversion("blah")
        table = self.memdb.getadvancedtable("blah")
        self.assertNotIn('b',table.columns)
        self.assertEqual(self.memdb.getversion(table),"1.0")

    def test_exampleusage(self):
        """ Double checks that the example usage is valid """

        db = VersionedDatabase(":memory:")

        db.addtables(Table("CREATE TABLE a (name TEXT);"))
        table = db.gettable("a")
        self.assertEqual(db.getversion(table), DotVersion("1.0"))

        update_script = "ALTER TABLE a ADD COLUMN value INTEGER;"
        rollback_script = generate_dropcolumn(table, "value")
        db.updateversion("a",updatescript = update_script, rollbackscript = rollback_script)
        table = db.gettable("a")
        self.assertEqual(db.getversion(table), DotVersion("2.0"))
        self.assertEqual(list(table.columns),["name","value"])

        db.rollbackversion(table)
        table = db.gettable("a")
        self.assertEqual(db.getversion(table), DotVersion("1.0"))
        self.assertEqual(list(table.columns), ["name",])

if __name__ == "__main__":
    unittest.main()
