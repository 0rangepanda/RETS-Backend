/**
 * jquery.hash
 * @author  ydr.me
 */

module.exports = function($) {
    'use strict';

    var
        udf,
        win = window,
        defaults = {
            hash: '',
            type: '!'
        },
        encode = encodeURIComponent,
        decode = decodeURIComponent,
        // [fn1, fn2, ...]
        listenAllCallbacks = [],
        listenOneMap = {},
        listenOrMap = {},
        listenAndMap = {},
        hashEqualMap = {
            '!': '/',
            '?': '='
        },
        hashSplitMap = {
            '!': '/',
            '?': '&'
        },
        regConstructorReplace = /^[^#]*/,
        regConstructorWhich = /^(#[^#]*)(#?.*)$/,
        isArray = $.isArray,
        inArray = $.inArray,
        each = $.each;



    $.hash = function(settings) {
        if ($.type(settings) === 'string') settings = {
            hash: settings
        };

        var options = $.extend({}, defaults, settings);
        options.hash = options.hash || win.location.hash;
        return new Constructor(options)._parse();
    };
    $.hash.defaults = defaults;


    $(win).bind('hashchange', function(eve) {
        var
            oe = eve.originalEvent,
            newRet = $.hash(oe.newURL).get(),
            oldRet = $.hash(oe.oldURL).get(),
            changeMap = {},
            changeKeys = [],
            changeKeysLength,
            oneCallbacks = [],
            orCallbacks = [],
            andCallbacks = [];

        each(newRet, function(key, val) {
            if (oldRet[key] !== val && changeMap[key] === udf) {
                changeMap[key] = {
                    'old': oldRet[key],
                    'new': val
                };
                changeKeys.push(key);
            }
        });

        each(oldRet, function(key, val) {
            if (newRet[key] !== val && changeMap[key] === udf) {
                changeMap[key] = {
                    'old': val,
                    'new': newRet[key]
                };
                changeKeys.push(key);
            }
        });

        if (!(changeKeysLength = changeKeys.length)) return;

        each(changeKeys, function(i, changeKey) {
            var andKeys, unfind;

            if (listenOneMap[changeKey]) {
                each(listenOneMap[changeKey].callbacks, function(index, callback) {
                    if (!~inArray(callback, oneCallbacks)) oneCallbacks.push(callback);
                });
            }

            if (listenOrMap[changeKey]) {
                each(listenOrMap[changeKey].callbacks, function(index, callback) {
                    if (!~inArray(callback, orCallbacks)) orCallbacks.push(callback);
                });
            }

            if (listenAndMap[changeKey]) {
                andKeys = listenAndMap[changeKey].keys;
                each(andKeys, function(index, key) {
                    if (!~inArray(key, changeKeys)) {
                        unfind = !0;
                        return !1;
                    }
                });

                if (!unfind) {
                    each(listenAndMap[changeKey].callbacks, function(index, callback) {
                        if (!~inArray(callback, andCallbacks)) andCallbacks.push(callback);
                    });
                }
            }
        });



        each(oneCallbacks, function(index, callback) {
            callback(newRet, oldRet);
        });
        each(orCallbacks, function(index, callback) {
            callback(newRet, oldRet);
        });
        each(andCallbacks, function(index, callback) {
            callback(newRet, oldRet);
        });
        each(listenAllCallbacks, function(index, callback) {
            callback(newRet, oldRet);
        });
    });


    // constructor

    function Constructor(options) {
        this.options = options;
    }

    Constructor.prototype = {
        _reset: function() {
            var the = this;
            the._equal = hashEqualMap[the._type];
            the._split = hashSplitMap[the._type];
        },

        _parse: function() {
            var
                the = this,
                options = the.options,
                hash = options.hash,
                matches,
                ret = {},
                arr,
                lastKey;

            hash = hash.replace(regConstructorReplace, '');
            if (hash[1] !== '!' && hash[1] !== '?') {
                the._type = options.type;
                the._reset();
                the._suffix = '';
                the._result = {};
                return the;
            }

            matches = hash.match(regConstructorWhich);
            the._hash = matches[1];
            the._suffix = matches[2];

            the._type = the._hash[1];
            the._reset();
            the._result = ret;

            the._hash = the._hash.replace(/^[#!?\/]+/, '');
            arr = the._hash.split(the._split);

            if (the._type === '!') {
                each(arr, function(index, val) {
                    if (index % 2) {
                        if (lastKey) ret[lastKey] = decode(val);
                    } else {
                        lastKey = val;
                        if (val) ret[val] = '';
                    }
                });
            }
        
            else if (the._type === '?') {
                each(arr, function(index, part) {
                    var pos = part.indexOf(the._equal),
                        key = part.slice(0, pos),
                        val = decode(part.slice(pos + 1));

                    if (key) ret[key] = val || '';
                });
            }

            the._result = ret;
            return the;
        },

        stringify: function(type) {
            var the = this,
                arr = [];

            if (type === '!' || type === '?') {
                the._type = type;
                the._reset();
            }

            each(the._result, function(key, val) {
                arr.push(key + the._equal + encode(val));
            });

            the._hash = the._type + arr.join(the._split);
            return '#' + the._hash + the._suffix;
        },

        location: function(type) {
            location.hash = this.stringify(type).replace(/^#+/, '');
        },

        set: function(key, val) {
            var
                map = {},
                the = this;
                
            // .set(obj)
            if (val === udf) map = key;
            // .set(str, str)
            else map[key] = val;

            $.extend(the._result, map);

            return the;
        },

        get: function(key) {
            if (key === udf) return this._result;

            var
                isMulitiple = isArray(key),
                keys = isMulitiple ? key : [key],
                ret = {},
                the = this;

            each(keys, function(index, key) {
                ret[key] = the._result[key];
            });

            return isMulitiple ? ret : ret[key];
        },

        remove: function(key) {
            var the = this;

            if (key === udf) {
                the._result = {};
                return the;
            }

            var
                isMulitiple = isArray(key),
                keys = isMulitiple ? key : [key];

            each(keys, function(index, key) {
                delete(the._result[key]);
            });

            return the;
        },

        listen: function() {
            var
                args = arguments,
                argL = args.length,
                arg0 = args[0],
                fn = args[argL - 1],
                isAnd = argL === 2 && isArray(arg0),
                isOr = argL > 2,
                isAll = argL === 1,
                isOne = !isAnd && !isOr && !isAll,
                keys = [],
                father;

            // .listen(fn)
            if (isAll) {
                father = listenAllCallbacks;
            }
            // .listen('key', fn)
            else if (isOne) {
                keys = [arg0];
                father = listenOneMap;
            }
            // listen('key1', 'key2', fn);
            else if (isOr) {
                keys = [].slice.call(args, 0, argL - 1);
                father = listenOrMap;
            }
            // listen(['key1', 'key2'], fn);
            else {
                keys = arg0;
                father = listenAndMap;
            }

            if (isAll) {
                if (!~inArray(fn, father)) father.push(fn);
            } else {
                each(keys, function(i, key) {
                    if (father[key] === udf) father[key] = {};
                    if (keys.length > 1 && father[key].keys === udf) father[key].keys = [];
                    if (father[key].callbacks == udf) father[key].callbacks = [];

                    var keysStack = father[key].keys,
                        callbacks = father[key].callbacks;

                    if (father[key].keys) each(keys, function(j, k) {
                        if (!~inArray(k, keysStack) && k !== key) keysStack.push(k);
                    });

                    if (!~inArray(fn, callbacks)) callbacks.push(fn);
                });
            }

            return this;
        },

        suffix: function(val) {
            var the = this;
            if (val === udf) return the._suffix;

            the._suffix = '#' + val;

            return the;
        }
    };

};