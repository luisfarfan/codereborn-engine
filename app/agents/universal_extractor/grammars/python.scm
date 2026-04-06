; Python Signals Query
; ---
; Imports
(import_statement) @import
(import_from_statement) @import

; Classes
(class_definition
  name: (identifier) @class_name
  superclasses: (argument_list)? @bases) @class

; Functions
(function_definition
  name: (identifier) @func_name) @func

; Decorators
(decorator) @decorator
