(module
    (import "imports" "logInt" (func $log_int (param i64)))
    (import "imports" "logBool" (func $log_bool (param i32)))
    (import "imports" "logString" (func $log_str (param i32)))
    (import "imports" "assert" (func $assert (param i32)))
    (memory (import "js" "mem") 1)
    (global $x (mut i32)
    i32.const 0
    )
    (global $y (mut i32)
    i32.const 0
    )
    (global $z (mut i32)
    i32.const 0
    )
    (func $main 
        (local $local_1 i32)
        (local $local_2 i32)
        (local $local_3 i32)
        i32.const 0
        i32.const 8
        i32.store
        i32.const 0
        i32.load
        local.tee $local_1
        i32.const 3
        i32.store
        i32.const 0
        i32.load
        i32.const 4
        i32.add
        i32.const 49
        i32.store8
        i32.const 0
        i32.load
        i32.const 5
        i32.add
        i32.const 50
        i32.store8
        i32.const 0
        i32.load
        i32.const 6
        i32.add
        i32.const 51
        i32.store8
        i32.const 0
        i32.const 8
        i32.const 0
        i32.load
        i32.add
        i32.store
        local.get $local_1
        global.set $x
        i32.const 0
        i32.load
        local.tee $local_2
        i32.const 0
        i32.store
        i32.const 0
        i32.const 8
        i32.const 0
        i32.load
        i32.add
        i32.store
        local.get $local_2
        global.set $y
        i32.const 0
        i32.load
        local.tee $local_3
        i32.const 5
        i32.store
        i32.const 0
        i32.load
        i32.const 4
        i32.add
        i32.const 49
        i32.store8
        i32.const 0
        i32.load
        i32.const 5
        i32.add
        i32.const 50
        i32.store8
        i32.const 0
        i32.load
        i32.const 6
        i32.add
        i32.const 51
        i32.store8
        i32.const 0
        i32.load
        i32.const 7
        i32.add
        i32.const 52
        i32.store8
        i32.const 0
        i32.load
        i32.const 8
        i32.add
        i32.const 53
        i32.store8
        i32.const 0
        i32.const 16
        i32.const 0
        i32.load
        i32.add
        i32.store
        local.get $local_3
        global.set $z
        global.get $x
        call $log_str
        global.get $y
        call $log_str
        global.get $z
        call $log_str
        global.get $x
        i32.load
        i64.extend_i32_u
        i64.const 3
        i64.eq
        call $assert
        global.get $y
        i32.load
        i64.extend_i32_u
        i64.const 0
        i64.eq
        call $assert
        global.get $z
        i32.load
        i64.extend_i32_u
        i64.const 5
        i64.eq
        call $assert
    )
    (start $main)
)