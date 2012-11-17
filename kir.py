#!/usr/bin/python
import os
import sys
import sqlite3
# With Python 2.4 and below, install PySqlite2: http://trac.edgewall.org/wiki/PySqlite
# and replace "import sqlite3" by "from pysqlite2 import dbapi2 as sqlite3"
from operator import itemgetter

PATH_CONFIG=""

keywords = {}
index = {}

db = sqlite3.connect(":memory:")

cursor = db.cursor()
cursor.execute("create virtual table rule using fts3(id, content)")

class Rule:
    def __init__( self, keywords, content ):
        self.keywords = set( keywords )
        self.content  = content


def read_config():

    lines = []
    fd = open( PATH_CONFIG, 'r' )
    lines = fd.readlines()
    fd.close()

    rules = []
    keywords_current = None
    content_current = None
    for line in lines:
        line = line.split('#')[ 0 ].strip('\n\r')
        #if not line: continue

        if line.startswith('rule'):
            if keywords_current:
                rules.append( Rule( keywords_current, content_current ) )
            keywords_current = [ token.strip(' ,') for token in line.strip().split()[ 1: ] ]
            content_current = []
        else:
            content_current.append( line )
            
    if keywords_current:
        rules.append( Rule( keywords_current, content_current ) )

    for rule in rules:
        is_empty = True
        content_new = []
        index_start = 0
        index_end = len( rule.content )
        for i in range( len( rule.content ) ):
            if rule.content[ i ].strip():
                index_start = i
                break

        for i in range( len( rule.content ) - 1, index_start - 1, -1 ):
            if rule.content[ i ].strip():
                index_end = i
                break

        rule.content = rule.content[ index_start : index_end + 1 ]

    return rules




def get_combinations( chosen, remaining ):
    out = []
    for i in range( len( remaining ) ):
        chosen_current = chosen + [ remaining[ i ] ]
        remaining_current = remaining[ i+1: ]
        out.append( chosen_current )
        out.extend( get_combinations( chosen_current, remaining_current ) )
    return out


def highlight_text( string, tokens_ ):
    tokens = set( tokens_ )
    words = string.split()
    result = []
    for word in words:
        if word in tokens:
            word_add = '\033[91m\033[1m' + word + '\033[0m'
        else:
            word_add = word
        result.append( word_add )
    return ' '.join( result )


if __name__=="__main__":
    try:
        rules = read_config()
        for index, r in enumerate( rules ):
            #pass
            #print "insert into rule (id, content) values ('%s', '%s')" % ( index, ' '.join( r.content ) )
            cursor.execute("insert into rule (id, content) values (?, ?)", ( index, ' '.join( r.keywords ) ) )

            for line in r.content:
                cursor.execute("insert into rule (id, content) values (?, ?)", ( index, line ) )
            #print r.keywords
            #print r.content
    except IOError, e:
        print e


    if len( sys.argv ) == 1:
        print 'Usage: howto [text to search]|[content id]' % ( sys.argv[ 0 ] )
    if len( sys.argv ) == 2 and sys.argv[ 1 ].isdigit():
        rule_id = int( float( sys.argv[ 1 ] ) )
        if rule_id < 0 or rule_id >= len( rules ):
            sys.exit( "Error, id is invalid" )

        for line in rules[ rule_id ].content:
            print line
    elif len( sys.argv ) >= 2:

        ids_found = set()
        ids_result = []
        combinations = get_combinations( [], sys.argv[1:] )
        combinations_sorted = sorted( combinations, key=len, reverse=True )
        #print combinations_sorted

        for c in combinations_sorted:
            for row in cursor.execute("select id, content from rule where content match '%s'" % ( ' '.join( c ) ) ):
                if row[ 0 ] not in ids_found:
                    ids_result.append( ( row[ 0 ], highlight_text( row[ 1 ], c ) ) )
                    ids_found.add( row[ 0 ] )

        if ids_result:
            print '%d results found' % len( ids_result )
            is_first = True
            for index, line in ids_result:
                if is_first:
                    is_first = False
                    print 'Best result:'
                    print '\033[94m\033[1m***\033[0m %4s: %s' % ( index, line )
                    print '-' * 64

                    for l in rules[ int(index) ].content:
                        print l

                    if len(ids_result) > 1:
                        print '*' * 64
                        print 'Other results:'
                        print '-' * 64
                else:

                    print '\033[94m\033[1m***\033[0m %4s: %s' % ( index, line )
        else:
            print 'Not result found.'
