Basic test commands and expected output:

```
# ./swarm-exec.py inst_exec '{"inst":[{"id":"oa4hd7dzkbjl"}],"command":"ls"}'
EXEC: task oa4hd7dzkbjl, node 64n4nk28c6okxx0ortqfhzu1k, container 22a797cad57a45398029b874c595fe60a60d52091553da5595bbb489121af63f, cmd "ls" (arguments stripped)
{
  "inst": [
    {
      "id": "oa4hd7dzkbjl"
    }
  ],
  "command": "ls"
}
```

```
# ./swarm-exec.py inst_exec '{"inst":[{"id":"oa4hd7dzkbjl"}],"command":"lsx"}'
EXEC: task oa4hd7dzkbjl, node 64n4nk28c6okxx0ortqfhzu1k, container 22a797cad57a45398029b874c595fe60a60d52091553da5595bbb489121af63f, cmd "lsx" (arguments stripped)
exitcode:126 (task state:"failed", message:"started", err:"task: non-zero exit (126)")
```

```
# ./swarm-exec.py inst_exec '{"inst":[{"id":"oa4hd7dzkbjl"}],"command":"false"}'
EXEC: task oa4hd7dzkbjl, node 64n4nk28c6okxx0ortqfhzu1k, container 22a797cad57a45398029b874c595fe60a60d52091553da5595bbb489121af63f, cmd "false" (arguments stripped)
exitcode:1 (task state:"failed", message:"started", err:"task: non-zero exit (1)")
```

```
# ./swarm-exec.py inst_exec '{"inst":[{"id":"oa4hd7dzkbjl"}],"command":"true"}'
EXEC: task oa4hd7dzkbjl, node 64n4nk28c6okxx0ortqfhzu1k, container 22a797cad57a45398029b874c595fe60a60d52091553da5595bbb489121af63f, cmd "true" (arguments stripped)
{
  "inst": [
    {
      "id": "oa4hd7dzkbjl"
    }
  ],
  "command": "true"
}
```

```
# ./swarm-exec.py inst_exec '{"inst":[{"id":"oa4hd7dzkbjl"}],"command":"sleep 5"}'
EXEC: task oa4hd7dzkbjl, node 64n4nk28c6okxx0ortqfhzu1k, container 22a797cad57a45398029b874c595fe60a60d52091553da5595bbb489121af63f, cmd "sleep" (arguments stripped)
{
  "inst": [
    {
      "id": "oa4hd7dzkbjl"
    }
  ],
  "command": "sleep 5"
}
```

```
# ./swarm-exec.py inst_exec '{"inst":[{"id":"oa4hd7dzkbjl"}],"command":"[\"sleep\",\"5\"]"}'
EXEC: task oa4hd7dzkbjl, node 64n4nk28c6okxx0ortqfhzu1k, container 22a797cad57a45398029b874c595fe60a60d52091553da5595bbb489121af63f, cmd "sleep" (arguments stripped)
{
  "inst": [
    {
      "id": "oa4hd7dzkbjl"
    }
  ],
  "command": "[\"sleep\",\"5\"]"
```