( examples/forth/fact_iter.forth )
: fact_iter ( n -- n! )
  1 swap        \ acc=1, n on top
  2 swap ?do    \ pseudo: start loop at 2; note: details depend on Forth dialect
    i *         \ acc = acc * i
  loop
;
\ Note: DO/LOOP semantics vary across Forth implementations. This is an idiomatic sketch.
