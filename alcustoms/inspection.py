def listImportablesFromAST(ast_):
    from ast import (Assign, ClassDef, FunctionDef, Import, ImportFrom, Name,
                     For, Tuple, With)

    if isinstance(ast_, (ClassDef, FunctionDef)):
        return [ast_.name]
    elif isinstance(ast_, (Import, ImportFrom)):
        return [name.asname if name.asname else name.name for name in ast_.names]

    ret = []

    if isinstance(ast_, Assign):
        for target in ast_.targets:
            if isinstance(target, Tuple):
                ret.extend([elt.id for elt in target.elts])
            elif isinstance(target, Name):
                ret.append(target.id)
        return ret

    # These two attributes cover everything of interest from If, Module,
    # and While. They also cover parts of For, TryExcept, TryFinally, and With.
    if hasattr(ast_, 'body') and isinstance(ast_.body, list):
        for innerAST in ast_.body:
            ret.extend(listImportablesFromAST(innerAST))
    if hasattr(ast_, 'orelse'):
        for innerAST in ast_.orelse:
            ret.extend(listImportablesFromAST(innerAST))

    if isinstance(ast_, For):
        target = ast_.target
        if isinstance(target, Tuple):
            ret.extend([elt.id for elt in target.elts])
        else:
            ret.append(target.id)
    # Appear to be deprecated: could not find pep for it
    #elif isinstance(ast_, TryExcept):
    #    for innerAST in ast_.handlers:
    #        ret.extend(listImportablesFromAST(innerAST))
    #elif isinstance(ast_, TryFinally):
    #    for innerAST in ast_.finalbody:
    #        ret.extend(listImportablesFromAST(innerAST))
    elif isinstance(ast_, With):
        if ast_.optional_vars:
            ret.append(ast_.optional_vars.id)
    return ret

def listImportablesFromSource(source, filename = '<Unknown>'):
    """ Given a document (string) source with optional file name, return a list of importable objects from that document """
    from ast import parse
    return listImportablesFromAST(parse(source, filename))

def listImportablesFromSourceFile(filename, encoding = "utf-8"):
    """ Given a path to a file, load that file as a string and parse the names of any importable python objects from the file.
    
        Accepts an optional encoding parameter for reading the file. If the file files on a SyntaxError the first time,
        the method will try again with "utf-8-sig" encoding to check if the SyntaxError was for a BOM.
    """
    with open(filename, encoding = encoding) as f:
        source = f.read()
    try:
        return listImportablesFromSource(source, filename)
    except SyntaxError as e:
        if encoding != 'utf-8-sig':
            return listImportablesFromSourceFile(filename,encoding = 'utf-8-sig')
        raise e