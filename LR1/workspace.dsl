workspace {
    !identifiers hierarchical
    name "cdek"
    description "Сервис доставки товаров"

    model {
        sender = person "Отправитель" {
            description "Пользователь, который отправляет посылки"
        }
        recipient = person "Получатель" {
            description "Пользователь, который получает посылки"
        }

        postalSystem = softwareSystem "Сервис управления отправлениями и доставками товаров" {
            description "Система для управления пользователями, посылками и доставками"

            db = container "База данных" {
                            technology "PostgreSQL"
                            description "Хранит информацию о пользователях, посылках и доставках."
                        }
            
            package  = container "Посылка" {
                technology "Java Spring"
                -> db "Создание/удаление записи о новой посылке" 
            }

            delivery  = container "Доставка" {
                description "Обрабатывает данные о доставках и управляет логистикой."
                technology "Java Spring"
                -> db "Получение инфорации о сроках доставке, месте выдачи и тп" 
            }

            api = container "API-сервис" {
                technology "Spring, REST API"
                description "Предоставляет API для управления пользователями, посылками и доставками."
            -> package "Создание/изменение/удаление информации о посылке. Получение информации о посылке"
            -> delivery "Создание/изменение/удаление доставки. Получение информации о доставке"
            -> db "Создание/изменение/удаление информации о пользователе"
            }

            web = container "Веб-приложение" {
                technology "JS, React"
                description "Предоставляет пользовательский интерфейс для взаимодействия с почтовым сервисом."
             -> api "Отправляет запросы через API"
            }
        
        }

        deliverySystem = softwareSystem "Служба доставки посылок" {
            description "Непосредственная доставка и получение посылок, выполняемая людьми и роботами"
         }
        sender -> postalSystem.web "Регистрируется, создает посылку, узнает статус доставки"
        recipient -> postalSystem.web "Регистрируется, узнает статус отправки"
        postalSystem -> deliverySystem "Передает информацию о необходимости выполнить приемку/доставку посылки"
        sender -> deliverySystem "Отправляет посылку"
        recipient -> deliverySystem "Получает посылку"

    }

    views {
        theme default
        systemContext postalSystem {
            include *
            autolayout lr
        }

        container postalSystem {
            include *
            autolayout lr
        }

        dynamic postalSystem "uc01" "Создание нового отправителя" {
            autolayout lr
            sender -> postalSystem.web "Запрос на регистрацию в сервисе"
            postalSystem.web -> postalSystem.api "Запрос на создание нового пользователя"
            postalSystem.api -> postalSystem.db "Подтверждение записи"
        }

        dynamic postalSystem "uc02" "Поиск пользователя по логину" {
            autolayout lr
            sender -> postalSystem.web "Запрос на поиск пользователя по логину"
            postalSystem.web -> postalSystem.api "Запрос на поиск пользователя по логину"
            postalSystem.api -> postalSystem.db "SELECT username FROM user where login={}"
        }

        dynamic postalSystem "uc03" "Поиск пользователя по маске имя и фамилии" {
            autolayout lr
            sender -> postalSystem.web "Запрос на поиск пользователя по маске имя и фамилии"
            postalSystem.web -> postalSystem.api "Запрос на поиск пользователя по логину"
            postalSystem.api -> postalSystem.db "SELECT username FROM user where name like {}..."
        }

        dynamic postalSystem "uc04" "Создание посылки" {
            autolayout lr
            sender -> postalSystem.web "POST /package/..."
            postalSystem.web -> postalSystem.api "POST /package/..."
            postalSystem.api -> postalSystem.package "POST /package/..."
            postalSystem.package -> postalSystem.db "INSERT INTO ..."
        }

        dynamic postalSystem "uc05" "Получение информации о доставке по получателю" {
            autolayout lr
            recipient -> postalSystem.web "GET /delivery/..."
            postalSystem.web -> postalSystem.api "GET /delivery/..."
            postalSystem.api -> postalSystem.delivery "GET /delivery/..."
            postalSystem.delivery -> postalSystem.db "SELECT ..."
        }

        dynamic postalSystem "uc06" "Получение информации о доставке по отправителю" {
            autolayout lr
            sender -> postalSystem.web "GET /delivery/..."
            postalSystem.web -> postalSystem.api "GET /delivery/..."
            postalSystem.api -> postalSystem.delivery "GET /delivery/..."
            postalSystem.delivery -> postalSystem.db "SELECT ..."
        }

        
}
}