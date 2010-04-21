# MySQL Connector/Python - MySQL driver written in Python.
# Copyright 2009 Sun Microsystems, Inc. All rights reserved
# Use is subject to license terms. (See COPYING)

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
# 
# There are special exceptions to the terms and conditions of the GNU
# General Public License as it is applied to this software. View the
# full text of the exception in file EXCEPTIONS-CLIENT in the directory
# of this software distribution or see the FOSS License Exception at
# www.mysql.com.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""Various MySQL constants and character sets
"""

from errors import ProgrammingError

class _constants(object):
    
    prefix = ''
    desc = {}
    
    def __new__(cls):
        raise TypeError, "Can not instanciate from %s" % cls.__name__
        
    @classmethod
    def get_desc(cls,name):
        res = ''
        try:
            res = cls.desc[name][1]
        except KeyError, e:
            raise KeyError, e
        else:
            return res
            
    @classmethod
    def get_info(cls,n):
        res = ()
        for k,v in cls.desc.items():
            if v[0] == n:
                return v[1]
        raise KeyError, e
    
    @classmethod
    def get_full_info(cls):
        res = ()
        try:
            res = ["%s : %s" % (k,v[1]) for k,v in cls.desc.items()]
        except StandardError, e:
            res = ('No information found in constant class.%s' % e)
        
        return res
            
class FieldType(_constants):
    
    prefix = 'FIELD_TYPE_'
    DECIMAL     = 0x00
    TINY        = 0x01
    SHORT       = 0x02
    LONG        = 0x03
    FLOAT       = 0x04
    DOUBLE      = 0x05
    NULL        = 0x06
    TIMESTAMP   = 0x07
    LONGLONG    = 0x08
    INT24       = 0x09
    DATE        = 0x0a
    TIME        = 0x0b
    DATETIME    = 0x0c
    YEAR        = 0x0d
    NEWDATE     = 0x0e
    VARCHAR     = 0x0f
    BIT         = 0x10
    NEWDECIMAL  = 0xf6
    ENUM        = 0xf7
    SET         = 0xf8
    TINY_BLOB   = 0xf9
    MEDIUM_BLOB = 0xfa
    LONG_BLOB   = 0xfb
    BLOB        = 0xfc
    VAR_STRING  = 0xfd
    STRING      = 0xfe
    GEOMETRY    = 0xff
    
    desc = {
        'DECIMAL':       (0x00, 'DECIMAL'),
        'TINY':          (0x01, 'TINY'),
        'SHORT':         (0x02, 'SHORT'),
        'LONG':          (0x03, 'LONG'),
        'FLOAT':         (0x04, 'FLOAT'),
        'DOUBLE':        (0x05, 'DOUBLE'),
        'NULL':          (0x06, 'NULL'),
        'TIMESTAMP':     (0x07, 'TIMESTAMP'),
        'LONGLONG':      (0x08, 'LONGLONG'),
        'INT24':         (0x09, 'INT24'),
        'DATE':          (0x0a, 'DATE'),
        'TIME':          (0x0b, 'TIME'),
        'DATETIME':      (0x0c, 'DATETIME'),
        'YEAR':          (0x0d, 'YEAR'),
        'NEWDATE':       (0x0e, 'NEWDATE'),
        'VARCHAR':       (0x0f, 'VARCHAR'),
        'BIT':           (0x10, 'BIT'),
        'NEWDECIMAL':    (0xf6, 'NEWDECIMAL'),
        'ENUM':          (0xf7, 'ENUM'),
        'SET':           (0xf8, 'SET'),
        'TINY_BLOB':     (0xf9, 'TINY_BLOB'),
        'MEDIUM_BLOB':   (0xfa, 'MEDIUM_BLOB'),
        'LONG_BLOB':     (0xfb, 'LONG_BLOB'),
        'BLOB':          (0xfc, 'BLOB'),
        'VAR_STRING':    (0xfd, 'VAR_STRING'),
        'STRING':        (0xfe, 'STRING'),
        'GEOMETRY':      (0xff, 'GEOMETRY'),
    }
    
    @classmethod
    def get_string_types(cls):
        return [
            cls.VARCHAR,
            cls.ENUM,
            cls.VAR_STRING, cls.STRING,
            ]
    
    @classmethod
    def get_binary_types(cls):
        return [
            cls.TINY_BLOB, cls.MEDIUM_BLOB,
            cls.LONG_BLOB, cls.BLOB,
            ]
    
    @classmethod
    def get_number_types(cls):
        return [
            cls.DECIMAL, cls.NEWDECIMAL,
            cls.TINY, cls.SHORT, cls.LONG,
            cls.FLOAT, cls.DOUBLE,
            cls.LONGLONG, cls.INT24,
            cls.BIT,
            cls.YEAR,
            ]
    
    @classmethod
    def get_timestamp_types(cls):
        return [
            cls.DATETIME, cls.TIMESTAMP,
            ]

class FieldFlag(_constants):
    """
    Field flags as found in MySQL sources mysql-src/include/mysql_com.h
    """
    _prefix = ''
    NOT_NULL             = 1 <<  0
    PRI_KEY              = 1 <<  1
    UNIQUE_KEY           = 1 <<  2
    MULTIPLE_KEY         = 1 <<  3
    BLOB                 = 1 <<  4
    UNSIGNED             = 1 <<  5
    ZEROFILL             = 1 <<  6
    BINARY               = 1 <<  7

    ENUM                 = 1 <<  8
    AUTO_INCREMENT       = 1 <<  9
    TIMESTAMP            = 1 << 10
    SET                  = 1 << 11

    NO_DEFAULT_VALUE     = 1 << 12
    ON_UPDATE_NOW        = 1 << 13
    NUM                  = 1 << 14
    PART_KEY             = 1 << 15
    GROUP                = 1 << 14    # SAME AS NUM !!!!!!!????
    UNIQUE               = 1 << 16
    BINCMP               = 1 << 17

    GET_FIXED_FIELDS     = 1 << 18
    FIELD_IN_PART_FUNC   = 1 << 19
    FIELD_IN_ADD_INDEX   = 1 << 20
    FIELD_IS_RENAMED     = 1 << 21

    desc = {
        'NOT_NULL':             (1 <<  0, "Field can't be NULL"),
        'PRI_KEY':              (1 <<  1, "Field is part of a primary key"),
        'UNIQUE_KEY':           (1 <<  2, "Field is part of a unique key"),
        'MULTIPLE_KEY':         (1 <<  3, "Field is part of a key"),
        'BLOB':                 (1 <<  4, "Field is a blob"),
        'UNSIGNED':             (1 <<  5, "Field is unsigned"),
        'ZEROFILL':             (1 <<  6, "Field is zerofill"),
        'BINARY':               (1 <<  7, "Field is binary  "),
        'ENUM':                 (1 <<  8, "field is an enum"),
        'AUTO_INCREMENT':       (1 <<  9, "field is a autoincrement field"),
        'TIMESTAMP':            (1 << 10, "Field is a timestamp"),
        'SET':                  (1 << 11, "field is a set"),
        'NO_DEFAULT_VALUE':     (1 << 12, "Field doesn't have default value"),
        'ON_UPDATE_NOW':        (1 << 13, "Field is set to NOW on UPDATE"),
        'NUM':                  (1 << 14, "Field is num (for clients)"),

        'PART_KEY':             (1 << 15, "Intern; Part of some key"),
        'GROUP':                (1 << 14, "Intern: Group field"),   # Same as NUM
        'UNIQUE':               (1 << 16, "Intern: Used by sql_yacc"),
        'BINCMP':               (1 << 17, "Intern: Used by sql_yacc"),
        'GET_FIXED_FIELDS':     (1 << 18, "Used to get fields in item tree"),
        'FIELD_IN_PART_FUNC':   (1 << 19, "Field part of partition func"),
        'FIELD_IN_ADD_INDEX':        (1 << 20, "Intern: Field used in ADD INDEX"),
        'FIELD_IS_RENAMED':          (1 << 21, "Intern: Field is being renamed"),
    }


class ServerCmd(_constants):
    _prefix = 'COM_'
    SLEEP           =  0
    QUIT            =  1
    INIT_DB         =  2 
    QUERY           =  3
    FIELD_LIST      =  4
    CREATE_DB       =  5
    DROP_DB         =  6
    REFRESH         =  7
    SHUTDOWN        =  8
    STATISTICS      =  9
    PROCESS_INFO    = 10
    CONNECT         = 11
    PROCESS_KILL    = 12
    DEBUG           = 13
    PING            = 14
    TIME            = 15
    DELAYED_INSERT  = 16
    CHANGE_USER     = 17
    BINLOG_DUMP     = 18
    TABLE_DUMP      = 19
    CONNECT_OUT     = 20
    REGISTER_SLAVE  = 21
    STMT_PREPARE    = 22
    STMT_EXECUTE    = 23
    STMT_SEND_LONG_DATA = 24
    STMT_CLOSE      = 25
    STMT_RESET      = 26
    SET_OPTION      = 27
    STMT_FETCH      = 28
    DAEMON          = 29

class ClientFlag(_constants):
    """
    Client Options as found in the MySQL sources mysql-src/include/mysql_com.h
    """
    LONG_PASSWD             = 1 << 0
    FOUND_ROWS              = 1 << 1
    LONG_FLAG               = 1 << 2
    CONNECT_WITH_DB         = 1 << 3
    NO_SCHEMA               = 1 << 4
    COMPRESS                = 1 << 5
    ODBC                    = 1 << 6
    LOCAL_FILES             = 1 << 7
    IGNORE_SPACE            = 1 << 8
    PROTOCOL_41             = 1 << 9
    INTERACTIVE             = 1 << 10
    SSL                     = 1 << 11
    IGNORE_SIGPIPE          = 1 << 12
    TRANSACTIONS            = 1 << 13
    RESERVED                = 1 << 14
    SECURE_CONNECTION       = 1 << 15
    MULTI_STATEMENTS        = 1 << 16
    MULTI_RESULTS           = 1 << 17
    SSL_VERIFY_SERVER_CERT  = 1 << 30
    REMEMBER_OPTIONS        = 1 << 31
    
    desc = {
        'LONG_PASSWD':        (1 <<  0, 'New more secure passwords'),
        'FOUND_ROWS':         (1 <<  1, 'Found instead of affected rows'),
        'LONG_FLAG':          (1 <<  2, 'Get all column flags'),
        'CONNECT_WITH_DB':    (1 <<  3, 'One can specify db on connect'),
        'NO_SCHEMA':          (1 <<  4, "Don't allow database.table.column"),
        'COMPRESS':           (1 <<  5, 'Can use compression protocol'),
        'ODBC':               (1 <<  6, 'ODBC client'),
        'LOCAL_FILES':        (1 <<  7, 'Can use LOAD DATA LOCAL'),
        'IGNORE_SPACE':       (1 <<  8, "Ignore spaces before ''"),
        'PROTOCOL_41':        (1 <<  9, 'New 4.1 protocol'),
        'INTERACTIVE':        (1 << 10, 'This is an interactive client'),
        'SSL':                (1 << 11, 'Switch to SSL after handshake'),
        'IGNORE_SIGPIPE':     (1 << 12, 'IGNORE sigpipes'),
        'TRANSACTIONS':       (1 << 13, 'Client knows about transactions'),
        'RESERVED':           (1 << 14, 'Old flag for 4.1 protocol'),
        'SECURE_CONNECTION':  (1 << 15, 'New 4.1 authentication'),
        'MULTI_STATEMENTS':   (1 << 16, 'Enable/disable multi-stmt support'),
        'MULTI_RESULTS':      (1 << 17, 'Enable/disable multi-results'),
        'SSL_VERIFY_SERVER_CERT':     (1 << 30, ''),
        'REMEMBER_OPTIONS':           (1 << 31, ''),
    }
    
    default = [
        LONG_PASSWD,
        LONG_FLAG,
        CONNECT_WITH_DB,
        PROTOCOL_41,
        TRANSACTIONS,
        SECURE_CONNECTION,
        MULTI_STATEMENTS,
        MULTI_RESULTS,
    ]

    @classmethod
    def get_default(cls):
        flags = 0
        for f in cls.default:
            flags |= f
        return flags

class ServerFlag(_constants):
    """
    Server flags as found in the MySQL sources mysql-src/include/mysql_com.h
    """
    _prefix = 'SERVER_'
    STATUS_IN_TRANS             = 1 << 0
    STATUS_AUTOCOMMIT           = 1 << 1
    MORE_RESULTS_EXISTS         = 1 << 3
    QUERY_NO_GOOD_INDEX_USED    = 1 << 4
    QUERY_NO_INDEX_USED         = 1 << 5
    STATUS_CURSOR_EXISTS        = 1 << 6
    STATUS_LAST_ROW_SENT        = 1 << 7
    STATUS_DB_DROPPED           = 1 << 8
    STATUS_NO_BACKSLASH_ESCAPES = 1 << 9

    desc = {
        'SERVER_STATUS_IN_TRANS':            (1 << 0, 'Transaction has started'),
        'SERVER_STATUS_AUTOCOMMIT':          (1 << 1, 'Server in auto_commit mode'),
        'SERVER_MORE_RESULTS_EXISTS':        (1 << 3, 'Multi query - next query exists'),
        'SERVER_QUERY_NO_GOOD_INDEX_USED':   (1 << 4, ''),
        'SERVER_QUERY_NO_INDEX_USED':        (1 << 5, ''),
        'SERVER_STATUS_CURSOR_EXISTS':       (1 << 6, ''),
        'SERVER_STATUS_LAST_ROW_SENT':       (1 << 7, ''),
        'SERVER_STATUS_DB_DROPPED':          (1 << 8, 'A database was dropped'),
        'SERVER_STATUS_NO_BACKSLASH_ESCAPES':   (1 << 9, ''),
    }

class RefreshOption(_constants):
    """Options used when sending the COM_REFRESH server command."""
    
    _prefix = 'REFRESH_'
    GRANT = 1 << 0
    LOG = 1 << 1
    TABLES = 1 << 2
    HOST = 1 << 3
    STATUS = 1 << 4
    THREADS = 1 << 5
    SLAVE = 1 << 6
    
    desc = {
        'GRANT': (1 << 0, 'Refresh grant tables'),
        'LOG': (1 << 1, 'Start on new log file'),
        'TABLES': (1 << 2, 'close all tables'),
        'HOSTS': (1 << 3, 'Flush host cache'),
        'STATUS': (1 << 4, 'Flush status variables'),
        'THREADS': (1 << 5, 'Flush thread cache'),
        'SLAVE': (1 << 6, 'Reset master info and restart slave thread'),
    }
    
class CharacterSet(_constants):
    """
    List of supported character sets with their collations. This maps to the
    character set we get from the server within the handshake packet.
    
    To update this list, use the following query:
      SELECT ID,CHARACTER_SET_NAME, COLLATION_NAME
         FROM INFORMATION_SCHEMA.COLLATIONS
         ORDER BY ID
    
    This list is hardcoded because we want to avoid doing each time the above
    query to get the name of the character set used.
    """
    
    _max_id = 211 # SELECT MAX(ID)+1 FROM INFORMATION_SCHEMA.COLLATIONS
    
    @classmethod
    def _init_desc(cls):
        if not cls.__dict__.has_key('desc'):
            
            # Do not forget to update the tests in test_constants!
            cls.desc = [ None for i in range(cls._max_id)]
            cls.desc[1] = ('big5','big5_chinese_ci')
            cls.desc[2] = ('latin2','latin2_czech_cs')
            cls.desc[3] = ('dec8','dec8_swedish_ci')
            cls.desc[4] = ('cp850','cp850_general_ci')
            cls.desc[5] = ('latin1','latin1_german1_ci')
            cls.desc[6] = ('hp8','hp8_english_ci')
            cls.desc[7] = ('koi8r','koi8r_general_ci')
            cls.desc[8] = ('latin1','latin1_swedish_ci')
            cls.desc[9] = ('latin2','latin2_general_ci')
            cls.desc[10] = ('swe7','swe7_swedish_ci')
            cls.desc[11] = ('ascii','ascii_general_ci')
            cls.desc[12] = ('ujis','ujis_japanese_ci')
            cls.desc[13] = ('sjis','sjis_japanese_ci')
            cls.desc[14] = ('cp1251','cp1251_bulgarian_ci')
            cls.desc[15] = ('latin1','latin1_danish_ci')
            cls.desc[16] = ('hebrew','hebrew_general_ci')
            cls.desc[18] = ('tis620','tis620_thai_ci')
            cls.desc[19] = ('euckr','euckr_korean_ci')
            cls.desc[20] = ('latin7','latin7_estonian_cs')
            cls.desc[21] = ('latin2','latin2_hungarian_ci')
            cls.desc[22] = ('koi8u','koi8u_general_ci')
            cls.desc[23] = ('cp1251','cp1251_ukrainian_ci')
            cls.desc[24] = ('gb2312','gb2312_chinese_ci')
            cls.desc[25] = ('greek','greek_general_ci')
            cls.desc[26] = ('cp1250','cp1250_general_ci')
            cls.desc[27] = ('latin2','latin2_croatian_ci')
            cls.desc[28] = ('gbk','gbk_chinese_ci')
            cls.desc[29] = ('cp1257','cp1257_lithuanian_ci')
            cls.desc[30] = ('latin5','latin5_turkish_ci')
            cls.desc[31] = ('latin1','latin1_german2_ci')
            cls.desc[32] = ('armscii8','armscii8_general_ci')
            cls.desc[33] = ('utf8','utf8_general_ci')
            cls.desc[34] = ('cp1250','cp1250_czech_cs')
            cls.desc[35] = ('ucs2','ucs2_general_ci')
            cls.desc[36] = ('cp866','cp866_general_ci')
            cls.desc[37] = ('keybcs2','keybcs2_general_ci')
            cls.desc[38] = ('macce','macce_general_ci')
            cls.desc[39] = ('macroman','macroman_general_ci')
            cls.desc[40] = ('cp852','cp852_general_ci')
            cls.desc[41] = ('latin7','latin7_general_ci')
            cls.desc[42] = ('latin7','latin7_general_cs')
            cls.desc[43] = ('macce','macce_bin')
            cls.desc[44] = ('cp1250','cp1250_croatian_ci')
            cls.desc[47] = ('latin1','latin1_bin')
            cls.desc[48] = ('latin1','latin1_general_ci')
            cls.desc[49] = ('latin1','latin1_general_cs')
            cls.desc[50] = ('cp1251','cp1251_bin')
            cls.desc[51] = ('cp1251','cp1251_general_ci')
            cls.desc[52] = ('cp1251','cp1251_general_cs')
            cls.desc[53] = ('macroman','macroman_bin')
            cls.desc[57] = ('cp1256','cp1256_general_ci')
            cls.desc[58] = ('cp1257','cp1257_bin')
            cls.desc[59] = ('cp1257','cp1257_general_ci')
            cls.desc[63] = ('binary','binary')
            cls.desc[64] = ('armscii8','armscii8_bin')
            cls.desc[65] = ('ascii','ascii_bin')
            cls.desc[66] = ('cp1250','cp1250_bin')
            cls.desc[67] = ('cp1256','cp1256_bin')
            cls.desc[68] = ('cp866','cp866_bin')
            cls.desc[69] = ('dec8','dec8_bin')
            cls.desc[70] = ('greek','greek_bin')
            cls.desc[71] = ('hebrew','hebrew_bin')
            cls.desc[72] = ('hp8','hp8_bin')
            cls.desc[73] = ('keybcs2','keybcs2_bin')
            cls.desc[74] = ('koi8r','koi8r_bin')
            cls.desc[75] = ('koi8u','koi8u_bin')
            cls.desc[77] = ('latin2','latin2_bin')
            cls.desc[78] = ('latin5','latin5_bin')
            cls.desc[79] = ('latin7','latin7_bin')
            cls.desc[80] = ('cp850','cp850_bin')
            cls.desc[81] = ('cp852','cp852_bin')
            cls.desc[82] = ('swe7','swe7_bin')
            cls.desc[83] = ('utf8','utf8_bin')
            cls.desc[84] = ('big5','big5_bin')
            cls.desc[85] = ('euckr','euckr_bin')
            cls.desc[86] = ('gb2312','gb2312_bin')
            cls.desc[87] = ('gbk','gbk_bin')
            cls.desc[88] = ('sjis','sjis_bin')
            cls.desc[89] = ('tis620','tis620_bin')
            cls.desc[90] = ('ucs2','ucs2_bin')
            cls.desc[91] = ('ujis','ujis_bin')
            cls.desc[92] = ('geostd8','geostd8_general_ci')
            cls.desc[93] = ('geostd8','geostd8_bin')
            cls.desc[94] = ('latin1','latin1_spanish_ci')
            cls.desc[95] = ('cp932','cp932_japanese_ci')
            cls.desc[96] = ('cp932','cp932_bin')
            cls.desc[97] = ('eucjpms','eucjpms_japanese_ci')
            cls.desc[98] = ('eucjpms','eucjpms_bin')
            cls.desc[128] = ('ucs2','ucs2_unicode_ci')
            cls.desc[129] = ('ucs2','ucs2_icelandic_ci')
            cls.desc[130] = ('ucs2','ucs2_latvian_ci')
            cls.desc[131] = ('ucs2','ucs2_romanian_ci')
            cls.desc[132] = ('ucs2','ucs2_slovenian_ci')
            cls.desc[133] = ('ucs2','ucs2_polish_ci')
            cls.desc[134] = ('ucs2','ucs2_estonian_ci')
            cls.desc[135] = ('ucs2','ucs2_spanish_ci')
            cls.desc[136] = ('ucs2','ucs2_swedish_ci')
            cls.desc[137] = ('ucs2','ucs2_turkish_ci')
            cls.desc[138] = ('ucs2','ucs2_czech_ci')
            cls.desc[139] = ('ucs2','ucs2_danish_ci')
            cls.desc[140] = ('ucs2','ucs2_lithuanian_ci')
            cls.desc[141] = ('ucs2','ucs2_slovak_ci')
            cls.desc[142] = ('ucs2','ucs2_spanish2_ci')
            cls.desc[143] = ('ucs2','ucs2_roman_ci')
            cls.desc[144] = ('ucs2','ucs2_persian_ci')
            cls.desc[145] = ('ucs2','ucs2_esperanto_ci')
            cls.desc[146] = ('ucs2','ucs2_hungarian_ci')
            cls.desc[192] = ('utf8','utf8_unicode_ci')
            cls.desc[193] = ('utf8','utf8_icelandic_ci')
            cls.desc[194] = ('utf8','utf8_latvian_ci')
            cls.desc[195] = ('utf8','utf8_romanian_ci')
            cls.desc[196] = ('utf8','utf8_slovenian_ci')
            cls.desc[197] = ('utf8','utf8_polish_ci')
            cls.desc[198] = ('utf8','utf8_estonian_ci')
            cls.desc[199] = ('utf8','utf8_spanish_ci')
            cls.desc[200] = ('utf8','utf8_swedish_ci')
            cls.desc[201] = ('utf8','utf8_turkish_ci')
            cls.desc[202] = ('utf8','utf8_czech_ci')
            cls.desc[203] = ('utf8','utf8_danish_ci')
            cls.desc[204] = ('utf8','utf8_lithuanian_ci')
            cls.desc[205] = ('utf8','utf8_slovak_ci')
            cls.desc[206] = ('utf8','utf8_spanish2_ci')
            cls.desc[207] = ('utf8','utf8_roman_ci')
            cls.desc[208] = ('utf8','utf8_persian_ci')
            cls.desc[209] = ('utf8','utf8_esperanto_ci')
            cls.desc[210] = ('utf8','utf8_hungarian_ci')

    @classmethod
    def get_info(cls,setid):
        """Returns information about the charset for given MySQL ID."""
        cls._init_desc()
        res = ()
        errmsg =  "Character set with id '%d' unsupported." % (setid)
        try:
            res = cls.desc[setid]
        except:
            raise ProgrammingError, errmsg

        if res is None:
            raise ProgrammingError, errmsg

        return res

    @classmethod
    def get_desc(cls,setid):
        """Returns info string about the charset for given MySQL ID."""
        res = ()
        try:
            res = "%s/%s" % self.get_info(setid)
        except ProgrammingError, e:
            raise
        else:
            return res
    
    @classmethod
    def get_charset_info(cls, name, collation=None):
        """Returns information about the charset and optional collation."""
        cls._init_desc()
        l = len(cls.desc)
        errmsg =  "Character set '%s' unsupported." % (name)
        
        if collation is None:
            collation = '%s_general_ci' % (name)
        
        # Search the list and return when found
        idx = 0
        for info in cls.desc:
            if info and info[0] == name and info[1] == collation:
                return (idx,info[0],info[1])
            idx += 1
        
        # If we got here, we didn't find the charset
        raise ProgrammingError, errmsg
        
    @classmethod
    def get_supported(cls):
        """Returns a list with names of all supproted character sets."""
        res = []
        for info in cls.desc:
            if info and info[0] not in res:
                res.append(info[0])
        return tuple(res)

    
