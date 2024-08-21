# Pydoo

Pydoo, the lightweight Python database framework to accelerate development

name idea from [Medoo](https://github.com/catfan/Medoo) for PHP

**Project in developing**...

## Features

* Lightweight - Portable with a simple module or source file.
* Easy - Easy to learn and use structure queries.
* Powerful - supports various common SQL queries, DDL and prevents SQL injections.
* Compatible - Supports MySQL, MSSQL, SQLite and more SQL engines.
* Friendly - Work with many Python distributions, and DBMS engines.
* Free - Under Apache license, free to use.

## Requirements

* Python 3.8+

## Get started

### Install via pip

Using pip to install pydoo

```shell
pip install pydoo
```

### Install via pip from requirements.txt

Using pip to install pydoo in requirements.txt

insert into `requirement.txt` in your project

```
pydoo==<any_version>
```

then using command below to install pydoo from `requirements.txt`

```shell
pip install -r requirements.txt
```

### Common use

```
from pydoo import Pydoo
import pymysql

MySQLConf = {
	'host': "host",
	'port': 3306,
	'user': "user",
	'password': "password",
	'database': "database",
	'charset': "utf8mb4",
}

connection = pymysql.connect(**MySQLConf)
cursor_generator = connection.cursor
doo = Pydoo(cursor_generator)

# SQL:
# Select col_a, col_b from TableA where col_a = 1 and col_b = 'ABC' limit 1
result = doo.table("TableA")
            .where("col_a", 1)
            .where("col_b", "ABC")
            .fields(("col_a", "col_b"))
            .limit(1)
            .select()
            
# SQL:
# Insert Into TableA (col_a, col_b) Value (1, 'ABC')
rows = doo.table("TableA")
          .insert({'col_a': 1, 'col_b': "ABC"})
          

```





