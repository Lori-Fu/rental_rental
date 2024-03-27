# coding:utf-8

class RET:
    OK                  = "0"
    DBERR               = "4001"
    NODATA              = "4002"
    DATAEXIST           = "4003"
    DATAERR             = "4004"
    SESSIONERR          = "4101"
    LOGINERR            = "4102"
    PARAMERR            = "4103"
    USERERR             = "4104"
    ROLEERR             = "4105"
    PWDERR              = "4106"
    REQERR              = "4201"
    IPERR               = "4202"
    THIRDERR            = "4301"
    IOERR               = "4302"
    SERVERERR           = "4500"
    UNKOWNERR           = "4501"

error_map = {
    RET.OK                    : u"success",
    RET.DBERR                 : u"database query failed",
    RET.NODATA                : u"no data",
    RET.DATAEXIST             : u"data already exists",
    RET.DATAERR               : u"wrong data",
    RET.SESSIONERR            : u"please log in",
    RET.LOGINERR              : u"log in failed",
    RET.PARAMERR              : u"invalid param",
    RET.USERERR               : u"user error",
    RET.ROLEERR               : u"user error",
    RET.PWDERR                : u"user error",
    RET.REQERR                : u"invalid request",
    RET.IPERR                 : u"IP error",
    RET.THIRDERR              : u"system error",
    RET.IOERR                 : u"file io error",
    RET.SERVERERR             : u"internal server error",
    RET.UNKOWNERR             : u"unknown error",
}
