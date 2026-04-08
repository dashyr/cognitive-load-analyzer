\ Conceptual RPN evaluator; actual implementation depends on available words.
\ This is a sketch showing how one might structure it.

: is-num ( c-addr u -- flag )  \ returns true if token is numeric (sketch)
  2drop true ;

: apply-op ( op -- )  \ pop two, apply
  \ ... implementation depends on control words
;

: eval-token ( addr u -- )
  is-num if
    >number? drop  \ push number (sketch)
  else
    apply-op
  then ;

: eval-rpn ( addr u -- n )
  \ parse space-separated tokens and call eval-token per token
;
