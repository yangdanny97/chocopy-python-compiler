(module
    (import "imports" "logInt" (func $log_int (param i64)))
    (import "imports" "logBool" (func $log_bool (param i32)))
    (import "imports" "logString" (func $log_str (param i64)))
    (import "imports" "assert" (func $assert (param i32)))
    (global $x (mut i64)
    i64.const 1
    )
    (global $y (mut i64)
    i64.const 2
    )
    (global $a (mut i32)
    i32.const 1
    )
    (global $b (mut i32)
    i32.const 0
    )
    (func $main 
        (local $local_1 i64)
        (local $local_2 i64)
        global.get $a
        (if
            (then
                i32.const 1
                call $assert
            )
            (else
                nop
            )
        )
        global.get $a
        (if
            (then
                i32.const 1
                call $assert
            )
            (else
                i32.const 0
                call $assert
            )
        )
        global.get $b
        (if
            (then
                i32.const 0
                call $assert
            )
            (else
                nop
            )
        )
        global.get $b
        (if
            (then
                i32.const 0
                call $assert
            )
            (else
                i32.const 1
                call $assert
            )
        )
        global.get $x
        global.get $y
        i64.eq
        (if
            (then
                i32.const 0
                call $assert
            )
            (else
                i32.const 1
                call $assert
            )
        )
        global.get $x
        global.get $x
        i64.eq
        (if
            (then
                i32.const 1
                call $assert
            )
            (else
                i32.const 0
                call $assert
            )
        )
        global.get $a
        (if
            (then
                i64.const 5
                local.set $local_1
            )
            (else
                i64.const 0
                local.set $local_1
            )
        )
        local.get $local_1
        i64.const 5
        i64.eq
        call $assert
        global.get $b
        (if
            (then
                i64.const 0
                local.set $local_2
            )
            (else
                i64.const 5
                local.set $local_2
            )
        )
        local.get $local_2
        i64.const 5
        i64.eq
        call $assert
    )
    (start $main)
)