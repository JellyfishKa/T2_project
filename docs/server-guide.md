# T2Project Server — Руководство по подключению и работе

## Общая информация

- **ОС:** Ubuntu 24.04.4 LTS (Server)
- **Hostname:** t2project
- **Пользователь:** jellyfishka
- **Tailscale IP:** `100.120.184.98`
- **Локальный IP:** `192.168.0.230`
- **Диск:** ~55 ГБ (ext4)

---

## Необходимое ПО

Для подключения к серверу каждому разработчику потребуется:

1. **Tailscale** — VPN-клиент для безопасного подключения к серверу.
   Скачать: [tailscale.com/download](https://tailscale.com/download)
   Поддерживаемые платформы: Windows, macOS, Linux, iOS, Android.

2. **SSH-клиент** — для работы с сервером через терминал.
   - Windows: встроенный OpenSSH (PowerShell/CMD) или [PuTTY](https://www.putty.org/)
   - macOS / Linux: встроенный терминал

3. **Git** — для работы с репозиториями.
   Скачать: [git-scm.com](https://git-scm.com/)

---

## Подключение к серверу

### Шаг 1: Установка и настройка Tailscale

1. Скачайте и установите Tailscale с [tailscale.com/download](https://tailscale.com/download).
2. Запустите приложение и авторизуйтесь — учётные данные и приглашение предоставит администратор сервера.
3. Убедитесь, что Tailscale активен (значок в трее / меню должен быть зелёным).

### Шаг 2: Подключение по SSH

Откройте терминал (PowerShell, CMD, Terminal) и выполните:

```bash
ssh jellyfishka@100.120.184.98
```

При первом подключении появится запрос:

```
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Введите **yes** целиком и нажмите Enter. Затем введите пароль.

### Шаг 3 (рекомендуется): Настройка SSH-ключей

Чтобы не вводить пароль каждый раз, настройте SSH-ключи.

**На своём компьютере** сгенерируйте ключ:

```bash
ssh-keygen -t ed25519
```

Нажимайте Enter на все вопросы (или задайте passphrase для дополнительной безопасности).

**Скопируйте публичный ключ на сервер:**

```bash
ssh-copy-id jellyfishka@100.120.184.98
```

Либо вручную — скопируйте содержимое файла `~/.ssh/id_ed25519.pub` и на сервере выполните:

```bash
echo "СОДЕРЖИМОЕ_ПУБЛИЧНОГО_КЛЮЧА" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

После этого подключение будет без пароля.

---

## Настройка Git и GitHub на сервере

### Установка Git (если отсутствует)

```bash
sudo apt update && sudo apt install -y git
```

### Базовая конфигурация

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "your@email.com"
```

### Подключение GitHub через SSH

1. Сгенерируйте SSH-ключ на сервере:

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

2. Скопируйте публичный ключ:

```bash
cat ~/.ssh/id_ed25519.pub
```

3. Добавьте его в GitHub: **Settings → SSH and GPG keys → New SSH key**.

4. Проверьте подключение:

```bash
ssh -T git@github.com
```

Должно появиться приветствие от GitHub.

### Клонирование репозитория

```bash
git clone git@github.com:ваш-пользователь/ваш-репозиторий.git
cd ваш-репозиторий
```

---

## Развёртывание сервиса

### Установка Docker (рекомендуемый способ)

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

Добавьте пользователя в группу docker (чтобы не писать sudo каждый раз):

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Типичный процесс деплоя

1. Клонируйте репозиторий (см. выше).
2. Перейдите в директорию проекта.
3. Если есть `docker-compose.yml`:

```bash
docker compose up -d
```

4. Если есть `Dockerfile`:

```bash
docker build -t my-app .
docker run -d -p 8080:8080 my-app
```

5. Проверьте, что сервис запущен:

```bash
docker ps
```

### Доступ к дашборду

После запуска сервис будет доступен по адресу:

```
http://100.120.184.98:ПОРТ
```

Где ПОРТ — порт, на котором работает ваше приложение (например, 8080, 3000 и т.д.).

---

## Полезные команды

| Команда | Описание |
|---------|----------|
| `ssh jellyfishka@100.120.184.98` | Подключение к серверу |
| `df -h` | Проверка свободного места на диске |
| `htop` | Мониторинг нагрузки (CPU, RAM) |
| `docker ps` | Список запущенных контейнеров |
| `docker compose logs -f` | Логи сервисов в реальном времени |
| `sudo reboot` | Перезагрузка сервера |
| `sudo shutdown now` | Выключение сервера |
| `tailscale status` | Статус Tailscale-подключений |

---

## Важные замечания

- Сервер работает только когда компьютер включён. При выключении доступ пропадает, но данные сохраняются.
- На этом же компьютере установлена Windows (dual boot). При загрузке GRUB предлагает выбор ОС. Для работы сервера выбирайте Ubuntu.
- Диск с Windows и HDD с файлами изолированы от сервера и не монтируются.
- Объём хранилища сервера ограничен ~55 ГБ — учитывайте это при деплое.
