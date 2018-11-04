# SecurIT Cup Git
----

## Описание
----

  Данный фремворк создан с целью объединить в себе максимальное количество утилит для всестороннего тестирования безопасности IoT устройств на всех уровнях реализации. Он обладает удобным графическим интерфейсом для работы с ним как с отдельным приложением, а так же возможностью импортирования его как библиотеки.

  Ключевыми аспектами инструмента стала гибкая модульная система с возможностью добавления своих модулей и их комбинирования. Фреймворк имеет возможность работать с тестируемым устройством на трех уровнях: hardware(интерфейсы отладки), software(реверс-инжиниринг ОС устройства) и communication(NRF24, Bluetooth, Wifi, ip-networking).


## Структура проекта
----

#### Внешний вид GUI:

![screen1.PNG](https://media.discordapp.net/attachments/140787642647183360/508668241418125313/screen1.PNG)
![screen2.PNG](https://media.discordapp.net/attachments/140787642647183360/508668274184028160/screen2.PNG)

#### Внешний вид версии для консоли:

![2018-11-04_18.49.19.png](https://media.discordapp.net/attachments/140787642647183360/508669169215078421/2018-11-04_18.49.19.png)


## Список модулей
----


![2018-11-04_18.45.45.png](https://cdn.discordapp.com/attachments/140787642647183360/508668411207876615/2018-11-04_18.45.45.png)

## Установка
----
#### Установка производиться командой: 

`python3 setup.py install`

## Зависимости
----

> Для работы фреймворка достаточно наличия модулей termcolor, tabulate, serial и scapy. Остальные > библиотеки, требуемые для функционирования модулей, импортируются в момент инициализации модуля  > (так как некоторые из них заточены под конкретные платформы и не могут быть установлены на любой  > системе) и должны быть установлены вручную при необходимости.


## Примеры использования
----

#### Пример использования фреймворка для дампа `/etc/passwd` с уязвимого устройства (ip-камера):

![](https://cdn.discordapp.com/attachments/140787642647183360/508646230633611274/ezgif.com-optimize.gif)

#### Для дампа всей директории `/etc/` с уязвимого устройства (ip-камера):

![Alt text](https://cdn.discordapp.com/attachments/140787642647183360/508654018432598016/ezgif.com-crop.gif)

![Картинка][image1]
![Картинка][image2]


[image1]: https://cdn.discordapp.com/attachments/140787642647183360/508664495883681792/image1.jpg
[image2]: https://media.discordapp.net/attachments/140787642647183360/508664821906931713/image0.jpg?width=1462&height=1097





## Примеры использования как библиотеки
----
###  Создание модуля
-----

Шаблон для написания нового модуля `/modules/[communication, firmware, hardware]/new_submodule`:
```python
#импорт функций фреймворка
from core.ISFFramework import ISFContainer, submodule


#обьявление модуля
@ISFContainer(version="1.0",
              author="Not_so_sm4rt_hom3 team")
class new_module:
    #обьявление аргументов, общих для всех субмодулей
    in_params = {
      "value_name1": Param("Описание переменной 1",
                         required=[False,True],
                         value_type=[str,int,bool,list,bytearray],
                         default_value=...),
      . . .
    }
    
    #обьявление возвращаемых переменных, общих для всех субмодулей 
    out_params = {
      "returned_val1": Param("Описание возвращаемой переменной 1",
                             value_type=...),
      . . .
    }
    
    
    
    
    #функция инициализации, обрабатывающая общие параметры
    def __init__(self,params):
        self.value_name1 = params["value_name1"]
    
    #обьявление субмодуля
    @submodule(name = "new_submodule",
               description = "Описание субмодуля",
               #Уникальные агументы субмодуля
               in_params = {
                  ...
               },
               #Уникальные возвращаемые значения субмодуля
               out_params = {
                  ...
               }
    def newSubmodule(self, params){
        . . .
      
      
        return {
            "returned_val1": ... ,
            . . .
        }
    }
               

```

### Использование модуля
-----

 ##### 1. Импорт

    from core import ISFFramework
  
 ##### 2. Пример кода
      
    ISFFramework.start()

    a = ISFFramework.get_container_class('hardware/Baudrate')

    b = a({
    'Device': '/dev/tty.usbserial-00000000',
    'Debug': True
    })

    baudrate = b.baudrateBruteforce({
    'Time': 1
    })['Baudrate'][0]

    print(baudrate)

## Скриншоты
-----

##### 1) Перехват адресов работающих на **nrf24** (`communication/NRF24/NRF24AddressFinder`)

![2018-11-03_14.02.59.png](https://cdn.discordapp.com/attachments/140787642647183360/508234687932661776/2018-11-03_14.02.59.png)
 
 
##### 2) Поиск устройств Bluetooth (`communication/Bluetooth/BluetoothFinder`)

![2018-11-02_0.17.35.png](https://media.discordapp.net/attachments/140787642647183360/507664569758515220/2018-11-02_0.17.35.png)

##### 3) Определяем скорость передачи данных (`communication/Baudrate/ClassicBruteforse`)

![2018-10-29_22.31.43-2.png](https://cdn.discordapp.com/attachments/140787642647183360/508676230913196032/2018-10-29_22.31.43-2.png)

## Заметки
----
- Фреймворк написан для python3.7 
- Для работы некоторых модулей(wi-fi) требуется сетевая карта с возможностью перехода в режим мониторинга. 
- Желательно наличие следующего оборудования: Arduino UNO, CrazyRadio PA и Ubertooth.


## Авторы
----
Илья Шапошников (@drakylar), Сергей Близнюк (@BronzeBee), Марахович София (@Soff_M)
 