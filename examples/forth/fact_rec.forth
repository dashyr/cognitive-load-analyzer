: fact_rec ( n -- n! )
  dup 1 <= if
    drop 1
  else
    dup 1 - recurse *
  then
;
