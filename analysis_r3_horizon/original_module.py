import ast,hashlib,types,pathlib
def load_original(path):
 path=pathlib.Path(path);source=path.read_text(encoding='utf-8-sig');tree=ast.parse(source,str(path))
 before={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 removed=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='main']
 tree.body=[n for n in tree.body if n not in removed]
 after={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};assert before==after
 module=types.ModuleType('unchanged_'+path.stem);module.__file__=str(path)
 exec(compile(tree,str(path),'exec'),module.__dict__)
 return module,{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'removed_top_level_main_calls':len(removed),'function_hashes_before':before,'function_hashes_after':after,'function_bodies_unchanged':True}
