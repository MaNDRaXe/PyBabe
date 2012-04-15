#!env/bin/python

from pybabe import Babe
from pybabe.base import MetaInfo
import unittest
import random
from cStringIO import StringIO
from pyftpdlib import ftpserver
from threading import Thread
import shutil, tempfile
import BaseHTTPServer, urllib2


def can_connect_to_the_net(): 
    try:
        socket.gethostbyname('www.google.com')
        return True
    except: 
        return False

class TestBasicFunction(unittest.TestCase):
        
    def test_keynormalize(self):
        self.assertEqual('Payant_Gratuit', MetaInfo.keynormalize('Payant/Gratuit'))
    
    def test_pull_process(self):
        babe = Babe()
        a = babe.pull(command=['/bin/ls', '-1', '.'], name='ls', names=['filename'], format="csv", encoding='utf8')
        a.push(filename='tests/ls.csv')
        
    def test_log(self):
        buf = StringIO()
        buf2 = StringIO()
        babe = Babe()
        a = babe.pull(filename='tests/test.csv', name='Test')
        a = a.log(logfile=buf)
        a.push(stream=buf2, format='csv')
        s = """foo	bar	f	d
1	2	3.2	2010/10/02
3	4	1.2	2011/02/02
"""
        self.assertEqual(s, buf.getvalue())
        self.assertEqual(s, buf2.getvalue())
        
        
test_csv_content = """foo\tbar\tf\td\n1\t2\t3.2\t2010/10/02\n3\t4\t1.2\t2011/02/02\n"""
        
class TestZip(unittest.TestCase):
    def test_zip(self):
        babe = Babe()
        a = babe.pull(filename='tests/test.csv', name='Test')
        a.push(filename='test.csv', compress='tests/test.zip')
        
    def test_zipread(self):
        babe = Babe()
        a = babe.pull(filename='tests/test_read.zip', name="Test")
        buf = StringIO() 
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), test_csv_content)
        
class TestFTP(unittest.TestCase):
    def setUp(self):
        self.port = random.choice(range(9000,11000))
        authorizer = ftpserver.DummyAuthorizer()
        self.dir = tempfile.mkdtemp()
        self.user = 'user'
        self.password = 'password'
        ftpserver.log = lambda x : None
        ftpserver.logline = lambda x : None
        authorizer.add_user(self.user, self.password, self.dir, perm='elradfmw')
        address = ('127.0.0.1', self.port)
        ftp_handler = ftpserver.FTPHandler
        ftp_handler.authorizer = authorizer 
        self.ftpd = ftpserver.FTPServer(address, ftp_handler)
        class RunServer(Thread):
            def run(self):
                try:
                    self.ftpd.serve_forever()
                except Exception: 
                    pass
        s = RunServer()
        s.ftpd = self.ftpd
        s.start()
 
        
    def tearDown(self):
        self.ftpd.close_all()
        if self.dir.startswith('/tmp'):
            shutil.rmtree(self.dir)
    
    def test_ftp(self):
        babe = Babe()
        a = babe.pull(filename='tests/test.csv', name='Test')
        a.push(filename='test.csv', protocol='ftp', user=self.user, password=self.password, host='localhost', port=self.port, protocol_early_check= False)
        b = babe.pull(filename='test.csv', name='Test', protocol='ftp', user=self.user, password=self.password, host='localhost', port=self.port)
        buf = StringIO()
        b.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), test_csv_content)
        
    def test_ftpzip(self):
        babe = Babe()
        a = babe.pull(filename='tests/test.csv', name='Test')
        a.push(filename='test.csv', compress='test.zip', protocol='ftp', user=self.user, password=self.password, host='localhost', port=self.port, protocol_early_check=False)
        
        
class TestCharset(unittest.TestCase):
    def test_writeutf16(self):
        babe = Babe()
        a = babe.pull(filename='tests/test.csv', name='Test')
        a.push(filename='tests/test_utf16.csv', encoding='utf_16')
        
    def test_cleanup(self):
        babe = Babe()
        a = babe.pull(filename='tests/test_badencoded.csv', utf8_cleanup=True, name='Test')
        a.push(filename='tests/test_badencoded_out.csv')

    def test_cleanup2(self):
        # Test no cleanup
        babe = Babe()
        a = babe.pull(filename='tests/test_badencoded.csv', name='Test')
        a.push(filename='tests/test_badencoded_out2.csv')

class TestSort(unittest.TestCase): 
    def test_sort(self):
        babe = Babe()
        s = '\n'.join(['k,v'] + [ '%u,%u' % (i,-i) for i in xrange(0,100001)])
        a = babe.pull(stream=StringIO(s), name='test', format='csv')
        a = a.typedetect()
        a = a.sort(key='v')
        a = a.head(n=1)
        buf = StringIO()
        a = a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'k,v\n100000,-100000\n')        

    def test_sortdiskbased(self):
        babe = Babe()
        s = '\n'.join(['k,v'] + [ '%u,%u' % (i,-i) for i in xrange(0,100001)])
        a = babe.pull(stream=StringIO(s), name='test', format='csv')
        a = a.typedetect()
        a = a.sort_diskbased(key='v', nsize=10000)
        a = a.head(n=1)
        buf = StringIO()
        a = a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'k,v\n100000,-100000\n')        

    
class TestExcel(unittest.TestCase):
    
    def test_excel_read_write(self):
        babe = Babe()
        b = babe.pull(filename='tests/test.xlsx', name='Test2').typedetect()
        b = b.mapTo(lambda row: row._replace(Foo=-row.Foo))
        b.push(filename='tests/test2.xlsx')

class TestTransform(unittest.TestCase):
    def test_split(self):
        babe = Babe()
        buf = StringIO("""a,b
1,3:4
2,7
""")
        a = babe.pull(stream=buf,format='csv',name='Test')
        a = a.split(column='b',separator=':')
        buf2 = StringIO()
        a.push(stream=buf2, format='csv')
        self.assertEquals(buf2.getvalue(), """a,b
1,3
1,4
2,7
""")

    s = 'city,b,c\nPARIS,foo,bar\nLONDON,coucou,salut\n'
    s2 = 'city,PARIS,LONDON\nb,foo,coucou\nc,bar,salut\n' 
    def test_transpose(self):
        a = Babe().pull(stream=StringIO(self.s), format='csv', primary_key='city').transpose()
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), self.s2)


class TestHTTP(unittest.TestCase):
    def setUp(self):
        self.port = random.choice(range(9000,11000))
        server_address = ('', self.port)
        class TestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/STOP":
                    self.send_response(200)
                    self.end_headers()
                    return 
                p = self.path.replace('/remote', 'tests')
                ff = open(p, 'rb')
                s = ff.read()
                self.send_response(200)
                self.send_header('Content-type',	'text/csv')
                self.end_headers()
                self.wfile.write(s)
                return 
            def log_request(self, code, size=None):
                pass
        class RunServer(Thread):
            def run(self):
                self.httpd = BaseHTTPServer.HTTPServer(server_address=server_address,  RequestHandlerClass=TestHandler)
                while self.keep_running:
                    self.httpd.handle_request()
        self.thread = RunServer()
        self.thread.keep_running = True
        self.thread.start()
    
    def tearDown(self):
        self.thread.keep_running = False
        try:
            k = urllib2.urlopen("http://localhost:%u/STOP" % self.port)
            k.read()
        except Exception:
            pass
        self.thread.join()
        self.thread = None
    
    def test_http(self):
        a = Babe().pull(protocol='http', host='localhost', name='Test', filename='remote/test.csv', port=self.port)
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'foo\tbar\tf\td\n1\t2\t3.2\t2010/10/02\n3\t4\t1.2\t2011/02/02\n')

class TestS3(unittest.TestCase):
    @unittest.skipUnless(can_connect_to_the_net(), 'Requires net connection')
    def test_s3(self):
        s = "a,b\n1,2\n3,4\n"
        buf1 = StringIO(s)
        a = Babe().pull(stream=buf1, format='csv', name='Test')
        a.push(filename='test3.csv', bucket='florian-test', protocol="s3") 
        b = Babe().pull(filename='test3.csv', name='Test', bucket='florian-test', protocol="s3")
        buf = StringIO() 
        b.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), s)
        
class TestMapTo(unittest.TestCase):
    def test_tuple(self):
        a = Babe().pull(filename='tests/test.csv', name='Test').typedetect()
        a = a.mapTo(lambda obj : obj._replace(foo=obj.foo + 1))
        buf = StringIO()
        a.push(stream=buf, format='csv')
        s = """foo	bar	f	d
2	2	3.2	2010-10-02
4	4	1.2	2011-02-02
"""
        self.assertEquals(buf.getvalue(), s) 
    
        
    def test_insert(self):
        a = Babe().pull(filename='tests/test.csv', name='Test').typedetect()
        a = a.mapTo(lambda row : row.foo+1, insert_columns=['fooplus'])
        buf = StringIO()
        a.push(stream=buf, format='csv')
        s = """foo	bar	f	d	fooplus
1	2	3.2	2010-10-02	2
3	4	1.2	2011-02-02	4
"""
        self.assertEquals(buf.getvalue(), s)
   
    def test_replace(self):
        a = Babe().pull(filename='tests/test.csv', name='Test').typedetect()
        a = a.mapTo(lambda row : [row.foo+1, row.bar*2], columns=['a','b'])
        buf = StringIO()
        a.push(stream=buf, format='csv')
        s = """a\tb\n2\t4\n4\t8\n"""
        self.assertEquals(buf.getvalue(), s)
        
class TestFlatMap(unittest.TestCase):
    def test_tuple(self):
        a = Babe().pull(stream=StringIO("a,b\n1,2:3\n4,5:6\n"), format="csv")
        a = a.flatMap(lambda row: [row._replace(b=i) for i in row.b.split(':')])
        buf = StringIO()
        a.push(stream=buf, format="csv")
        self.assertEquals(buf.getvalue(), "a,b\n1,2\n1,3\n4,5\n4,6\n")

class TestGroup(unittest.TestCase):
    def test_groupby(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.groupBy(key="a", reducer=lambda key, rows: (key, sum([row.b for row in rows])))
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), "a,b\n1,6\n3,4\n")
        
    def test_groupAll(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.groupAll(reducer=lambda rows: (max([row.b for row in rows]),), columns=['max'])
        buf = StringIO()
        a.push(stream=buf, format="csv")
        self.assertEquals(buf.getvalue(), "max\n4\n")
        
class TestFilterColumns(unittest.TestCase):
    def test_filter(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.filterColumns(keep_columns=['a'])
        buf = StringIO()
        a.push(stream=buf, format="csv")
        self.assertEquals(buf.getvalue(), "a\n1\n3\n1\n")
    
    def test_filter2(self):
         a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
         a = a.filterColumns(remove_columns=['a'])
         buf = StringIO()
         a.push(stream=buf, format="csv")
         self.assertEquals(buf.getvalue(), "b\n2\n4\n4\n")    
        
class TestFilter(unittest.TestCase):
    def test_filter(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.filter(function=lambda x : x.a == 3)
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'a,b\n3,4\n')
    #def test_groupby_sum(self):
    #    a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
    #    a = a.groupBy(key="a", reducer=lambda rows: rows + rows[0]._replace(b=sum([row.b for row in rows])))
    #    buf = StringIO()
    #    a.push(stream=buf, format='csv')
    #    self.assertEquals(buf.getvalue(), "a,b,sum\n1,2,\n1,4,\n,,6\n3,4,\n,,4\n")

class TestMinMax(unittest.TestCase):
    def test_max(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.maxN(column='b', n=2)
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'a,b\n3,4\n1,4\n')
        
    def test_min(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.minN(column='a', n=2)
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'a,b\n1,2\n1,4\n')
        
class TestRename(unittest.TestCase):
    def test_rename(self):
        a = Babe().pull(stream=StringIO('a,b\n1,2\n3,4\n1,4\n'), format="csv").typedetect()
        a = a.rename(a="c")
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), 'c,b\n1,2\n3,4\n1,4\n')

class TestWindowMap(unittest.TestCase):
    def test_windowMap(self):
        a = Babe().pull(stream=StringIO('a\n1\n2\n3\n4\n5\n6\n7\n'), format="csv").typedetect()
        a = a.windowMap(3, lambda rows : rows[-1]._make([sum([row.a for row in rows])]))
        buf = StringIO()
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), '"a"\n1\n3\n6\n9\n12\n15\n18\n')
        
class TestTwitter(unittest.TestCase):
    @unittest.skipUnless(can_connect_to_the_net(), 'Requires net connection')
    def test_twitter(self):
        a = Babe().pull_twitter()
        a = a.filterColumns(keep_columns=
        ["author_name", "author_id", "author_screen_name", "created_at", "hashtags", "text", "in_reply_to_status_id_str"])
        a = a.typedetect()
        buf = StringIO()
        a.push(stream=buf, format='csv')
    
class TestMongo(unittest.TestCase):
    s1 = 'rown,f,s\n1,4.3,coucou\n2,4.2,salut\n'
    s2 = 'rown,f,s\n1,4.3,coucou2\n2,4.2,salut2\n'
    def test_push(self):
        a  = Babe().pull(stream=StringIO(self.s1), format='csv', primary_key='rown')
        a = a.typedetect()
        a.push_mongo(db='pybabe_test',collection='test_push')

    def test_pushpull(self):
        a  = Babe().pull(stream=StringIO(self.s2), format='csv', primary_key='rown')
        a = a.typedetect()
        a.push_mongo(db='pybabe_test',collection='test_pushpull')
        b = Babe().pull_mongo(db="pybabe_test", names=['rown', 'f', 's'], collection='test_pushpull')
        buf = StringIO()
        b.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), self.s2)      

class TestDedup(unittest.TestCase):
    s = 'id,value,s\n1,coucou,4\n2,blabla,5\n3,coucou,6\n4,tutu,4\n'
    s2 = 'id,value,s\n1,coucou,4\n1,coucou,4\n3,coucou,6\n4,tutu,4\n'
    s3 = 'id,value,s\n1,coucou,4\n3,coucou,6\n4,tutu,4\n'
    s4 = 'id,value,s\n1,coucou,4\n2,blabla,5\n4,tutu,4\n'

    def test_dedup1(self):
        a = Babe().pull(stream=StringIO(self.s), format="csv")
        a = a.dedup()
        buf = StringIO()
        a.push(stream=buf,format="csv")
        self.assertEquals(buf.getvalue(), self.s)

    def test_dedup2(self): 
        a = Babe().pull(stream=StringIO(self.s2), format="csv")
        a = a.dedup()
        buf = StringIO()
        a.push(stream=buf,format="csv")
        self.assertEquals(buf.getvalue(), self.s3)

    def test_dedup3(self):
        a = Babe().pull(stream=StringIO(self.s2), format="csv")
        a = a.dedup(columns=['id'])
        buf = StringIO()
        a.push(stream=buf,format="csv")
        self.assertEquals(buf.getvalue(), self.s3)

    def test_dedup4(self):
        a = Babe().pull(stream=StringIO(self.s), format="csv")
        a = a.dedup(columns=['value'])
        buf = StringIO()
        a.push(stream=buf,format="csv")
        self.assertEquals(buf.getvalue(), self.s4)





class TestPrimaryKey(unittest.TestCase):
    s = 'id,value,s\n1,coucou,4\n2,blabla,5\n3,coucou,6\n4,tutu,4\n'

    s2 = 'id,value,s\n1,coucou,4\n2,blabla,5\n3,coucou,6\n4,tutu,7\n'

    s3 = 'id,value,s\n1,coucou,4\n2,blabla,5\n3,coucou,6\n1,tutu,4\n'

    def test_primarykey(self):
        a = Babe().pull(stream=StringIO(self.s), format='csv')
        a = a.primary_key_detect().dedup(primary_keys=True)
        buf = StringIO() 
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), self.s)

    def test_primarykey2(self):
        a = Babe().pull(stream=StringIO(self.s2), format='csv')
        a = a.primary_key_detect().dedup(primary_keys=True)
        buf = StringIO() 
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), self.s2)        

    def test_primarykey3(self):
        a = Babe().pull(stream=StringIO(self.s3), format='csv')
        a = a.primary_key_detect().dedup(primary_keys=True)
        buf = StringIO() 
        a.push(stream=buf, format='csv')
        self.assertEquals(buf.getvalue(), self.s3)

    def test_airport(self):
        a = Babe().pull(filename='data/airports.csv')
        a = a.primary_key_detect().dedup(primary_keys=True)
        a = a.head(n=10)
        buf = StringIO() 
        a.push(stream=buf, format='csv')

class TestBuzzData(unittest.TestCase):
    @unittest.skipUnless(can_connect_to_the_net(), 'Requires net connection')
    @unittest.skipUnless(Babe.has_config('buzzdata', 'api_key'), 'Requires Buzzdata api Key')
    def test_buzzdata(self):
        a = Babe().pull(protocol='buzzdata', 
                dataset='best-city-contest-worldwide-cost-of-living-index',
                 username='eiu', format='xls')
        a = a.head(2)
        buf = StringIO()
        a.push(stream=buf, format='csv')


class TestSQL(unittest.TestCase):
    s = 'id,value,s\n1,coucou,4\n2,blabla,5\n3,coucou,6\n4,tutu,4\n'

    def test_pushsqlite(self):
        a = Babe().pull(stream=StringIO(self.s), format='csv')
        a = a.typedetect()
        a.push_sql(table='test_table', database_kind='sqlite', database='test.sqlite', drop_table = True, create_table=True)
        b = Babe().pull_sql(database_kind='sqlite', database='test.sqlite', table='test_table')
        buf = StringIO()
        b.push(stream=buf, format='csv', delimiter=',')
        self.assertEquals(buf.getvalue(), self.s)

    def test_mysql(self):
        a = Babe().pull(stream=StringIO(self.s), format='csv')
        a = a.typedetect()
        a.push_sql(table='test_table', database_kind='mysql', database='pybabe_test', drop_table = True, create_table=True)
        b = Babe().pull_sql(database_kind='mysql', database='pybabe_test', table='test_table')
        buf = StringIO()
        b.push(stream=buf, format='csv', delimiter=',')
        self.assertEquals(buf.getvalue(), self.s)

import code, traceback, signal

def debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    d={'_frame':frame}         # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message  = "Signal recieved : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)

def listen():
    signal.signal(signal.SIGUSR1, debug)  # Register handler
    
listen()

if __name__ == "__main__":
    unittest.main()