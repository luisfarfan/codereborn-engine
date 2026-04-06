; TypeScript Signals Query
; ---
; Imports
(import_statement source: (string) @import)

; Classes
(class_declaration name: (identifier) @class_name) @class

; Functions
(function_declaration name: (identifier) @func_name) @func

; Interfaces & Types
(interface_declaration name: (type_identifier) @type_name) @type
(type_alias_declaration name: (type_identifier) @type_name) @type

; Exports
(export_statement) @export
