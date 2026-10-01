# Лабораторная работа: вариант B

## Среда

Ubuntu Server в VirtualBox.
Подключение через SSH из Terminal на MacBook Air M1.
Фактические сведения о системе приведены в журнале environment.

## Файлы и запуск

- python3 ptree.py
- python3 runner.py 3 -- sleep 2
- python3 zombie.py
- python3 orphan.py
- python3 cow.py

## Дерево процессов

ptree.py читает /proc/PID/status без использования ps.
Выбирает процессы текущего пользователя по реальному UID.
Строит дерево по PPID, выводит PID, состояние и RSS в KiB.

## Запуск команд

runner.py создаёт N дочерних процессов через os.fork.
Каждый ребёнок запускает переданную команду через os.execvp.
Родитель забирает статусы через os.waitpid и выводит коды завершения.
Время измеряется от начала создания ребёнка до получения его статуса.
При прерывании оставшиеся прямые дети завершаются и собираются.

## Зомби

Ребёнок завершается с кодом 42.
До получения статуса родителем ps показывает состояние Z.
После os.waitpid запись ребёнка исчезает.

## Сирота

Родитель завершается раньше ребёнка.
PPID ребёнка изменился с 1458 на 1.

Сироту усыновил системный init с PID 1. Чтобы проверить, что это systemd, выполните readlink -f /sbin/init.

Фактическая строка усыновителя:

```text
1       0 Ss   12160 /sbin/init
```

Наблюдатель не назначается subreaper.
Он ждёт исчезновения сироты из /proc.
Статус сироты забирает её реальный новый родитель.

## Ленивое копирование памяти

Большой список создаётся до fork.
Ребёнок измеряет RSS, PSS и приватную память до и после
поэлементного изменения унаследованного списка.
Родитель сохраняет свой список и ждёт ребёнка.

После fork страницы первоначально используются совместно.
При записи возникают приватные копии страниц.
Приватная память и PSS ребёнка существенно растут.
RSS может почти не измениться: общие резидентные страницы
уже учитывались в RSS до записи.

У ребёнка элементы становятся равны 1,
а у родителя остаются равны 0.

## Проверка очистки

Результат проверки оставшихся процессов через ps
приведён в журнале cleanup.
При успешном завершении там присутствует сообщение:
OK: no recorded demo processes remain.

## Контрольные вопросы

1. Почему fork возвращает два разных значения?

После fork выполнение продолжается в двух процессах.
Родитель получает PID ребёнка, ребёнок получает 0.
Это позволяет различать родительскую и дочернюю ветки.
В Python ошибка fork вызывает OSError.

2. Что изменится, если вызвать exec без предварительного fork?

Новый процесс создан не будет.
Программа текущего процесса заменится другой, PID сохранится.
При успешном exec возврата в прежний код не произойдёт.
При ошибке os.execvp вызовет исключение.

## Сборка

Работа выполнена на Python.
Требования make и -Wall -Wextra относятся к реализации на C.

## Журнал: environment

```text
Linux 6.8.0-142-generic aarch64
PRETTY_NAME="Ubuntu 24.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.5 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
Python 3.12.3
uid=1000(mdnv) gid=1000(mdnv) groups=1000(mdnv),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),101(lxd)
    PID    PPID STAT COMMAND
      1       0 Ss   /sbin/init
```

## Журнал: ptree

```text
UID=1000; RSS in KiB
PID=1318 PPID=1 STATE=S RSS=10724 KiB NAME='systemd'
  PID=1320 PPID=1318 STATE=S RSS=3428 KiB NAME='(sd-pam)'
PID=1386 PPID=1313 STATE=S RSS=6544 KiB NAME='sshd'
  PID=1387 PPID=1386 STATE=S RSS=5272 KiB NAME='bash'
    PID=1411 PPID=1387 STATE=R RSS=11088 KiB NAME='python3'
    PID=1412 PPID=1387 STATE=S RSS=1848 KiB NAME='tee'
```

## Журнал: runner

```text
START #1 PID=1416
START #2 PID=1417
START #3 PID=1418
END #1 PID=1416 code=0 time=2.006s
END #2 PID=1417 code=0 time=2.005s
END #3 PID=1418 code=0 time=2.005s
```

## Журнал: runner_error

```text
START #1 PID=1441
START #2 PID=1442
END #1 PID=1441 code=7 time=0.003s
END #2 PID=1442 code=7 time=0.002s
```

## Журнал: zombie

```text
Parent PID=1450, zombie PID=1452
    PID    PPID STAT   RSS COMMAND
   1450    1387 S+   11056 python3 zombie.py
   1452    1450 Z+       0 [python3] <defunct>
Zombie visible; waitpid in 2 seconds.
Reaped PID=1452, code=42
After waitpid: only the header should remain.
    PID    PPID STAT   RSS COMMAND
```

## Журнал: orphan

```text
Orphan PID=1459: PPID 1458 -> 1
Orphan and its actual adopter:
    PID    PPID STAT   RSS COMMAND
      1       0 Ss   12160 /sbin/init
   1459       1 S+    9160 python3 orphan.py
Orphan finished and was reaped. No demo processes remain.
```

## Журнал: cow

```text
List: 4000000 elements
PARENT before fork: PID=1469 RSS=43348 KiB PSS=39279 KiB PRIVATE=37092 KiB
CHILD before write: PID=1471 RSS=41204 KiB PSS=19983 KiB PRIVATE=860 KiB
CHILD after write: PID=1471 RSS=41268 KiB PSS=35660 KiB PRIVATE=32172 KiB
CHILD data[0]=1 data[-1]=1
PARENT data[0]=0 data[-1]=0
Child code=0
```

## Журнал: cleanup

```text
Checking recorded PIDs: 1416, 1417, 1418, 1441, 1442, 1450, 1452, 1459, 1469, 1471
    PID    PPID STAT   RSS COMMAND
OK: no recorded demo processes remain.
```
