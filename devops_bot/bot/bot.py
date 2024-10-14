import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import re
import os
import psycopg2
from dotenv import load_dotenv
import paramiko
import subprocess

logging.basicConfig(filename='logs.txt', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

load_dotenv()
TOKEN = os.getenv('TOKEN')
RM_HOST = os.getenv('RM_HOST')
RM_PORT = os.getenv('RM_PORT')
RM_USER = os.getenv('RM_USER')
RM_PASSWORD = os.getenv('RM_PASSWORD')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_REPL_USER = os.getenv('DB_REPL_USER')
DB_REPL_PASSWORD = os.getenv('DB_REPL_PASSWORD')
DB_REPL_HOST = os.getenv('DB_REPL_HOST')
DB_REPL_PORT = os.getenv('DB_REPL_PORT')

# ssh
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(RM_HOST, username=RM_USER, password=RM_PASSWORD)
    print("SSH-соединение установлено успешно.")
except paramiko.AuthenticationException:
    print("Ошибка аутентификации. Проверьте имя пользователя и пароль.")
    ssh = None
except paramiko.SSHException as e:
    print(f"Общая ошибка SSH: {e}")
    ssh = None
except Exception as e:
    print(f"Ошибка подключения: {e}")
    ssh = None
#end.

#start of postgre
conn = psycopg2.connect(
    database=DB_DATABASE,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()
#end

#start of email
async def find_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Введите текст где искать адреса электронных почт:')
    return 1

async def find_email_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    if emails:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Найденные адреса: ' + ', '.join(emails))
        await update.message.reply_text('Записать в базу данных? (y/n)')
        context.user_data['emails'] = emails
        return 2
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Адреса не найдены')
    return ConversationHandler.END

async def save_email_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'y':
        emails = context.user_data.get('emails')
        for email in emails:
            cur.execute("INSERT INTO emails (email) VALUES (%s)", (email,))
        conn.commit()
        await update.message.reply_text('Данные успешно сохранены в базу данных')
    else:
        await update.message.reply_text('Данные не сохранены')
    return ConversationHandler.END

#end

#start of phone_number
async def find_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Введите текст для поиска номеров телефонов:')
    return 1

async def find_phone_number_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    phones = re.findall(r'(\+?7|8)?[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{2})[\s.-]?(\d{2})', text)
    if phones:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Найденные номера телефонов: ' + ', '.join([''.join(phone) for phone in phones]))
        await update.message.reply_text('Записать в базу данных? (y/n)')
        context.user_data['phones'] = phones
        return 2
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Номера телефонов не найдены')
    return ConversationHandler.END

async def save_phone_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'y':
        phones = context.user_data.get('phones')
        for phone in phones:
            cur.execute("INSERT INTO phone_numbers (phone_number) VALUES (%s)", (''.join(phone),))
        conn.commit()
        await update.message.reply_text('Данные успешно сохранены в базу данных')
    else:
        await update.message.reply_text('Данные не сохранены')
    return ConversationHandler.END
#end

#start of verify password
async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Введите пароль для проверки сложности')
    return 1

async def verify_password_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$ !%*#?&])[A-Za-z\d@$ !%*#?&]{8,}$'
    if re.match(pattern, password):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Пароль сложный')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Пароль простой')
    return ConversationHandler.END
#end

#start of system check commands
async def get_release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('sudo cat /etc/os-release')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('sudo uptime')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_df(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('sudo df -h')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_free(update: Update, context: ContextTypes.DEFAULT_TYPE):

    stdin, stdout, stderr = ssh.exec_command('sudo free -h')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_mpstat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('sudo mpstat')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_w(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('w')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_auths(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('last | head -n 10')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_uname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('uname -a')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_critical(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('dmesg | grep -i error | tail -n 5')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_ps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('ps aux')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)

async def get_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('ss -tlnp')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)
#end

#other information ftom server
async def get_apt_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Введите название пакета или напишите "all" для вывода всех пакетов:')
    return 1

async def get_apt_list_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.lower() == 'all':
        stdin, stdout, stderr = ssh.exec_command('dpkg --list | tail -n 5')
        output = stdout.read().decode('utf-8')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    else:
        stdin, stdout, stderr = ssh.exec_command(f'dpkg --list | grep {text}')
        output = stdout.read().decode('utf-8')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    return ConversationHandler.END

async def get_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('systemctl | tail -n 5')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)
#end

#help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Список команд:
/find_email - найти адреса электронных почт в тексте и по желанию записать их в базу
/find_phone_number - найти номера телефонов в тексте и по желанию записать их в базу
/verify_password - проверить сложность пароля
/get_release - получить информацию о релизе
/get_uname - получить информацию об архитектуре процессора, имени хоста системы и версии ядра
/get_uptime - получить информацию о времени работы
/get_df - получить информацию о состоянии файловой системы
/get_free - получить информацию о состоянии оперативной памяти
/get_mpstat - получить информацию о производительности системы
/get_w - получить информацию о работающих в данной системе пользователях
/get_auths - получить последние 10 входов в систему
/get_critical - получить последние 5 критических событий
/get_ps - получить информацию о запущенных процессах
/get_ss - получить информацию об используемых портах
/get_apt_list - получить информацию об установленных пакетах
/get_services - получить информацию о запущенных сервисах
/get_repl_logs - инфа о логах репликации
/get_emails - вывести адреса почт
/get_phone_numbers - вывести номера
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)
#end

#start of log
async def get_repl_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stdin, stdout, stderr = ssh.exec_command('cat /var/log/postgresql/postgresql-14-main.log | tail -n 5')
    output = stdout.read().decode('utf-8')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=output)
#end

#db_telegram_output
async def get_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cur.execute("SELECT email FROM emails;")
        emails = [row[0] for row in cur.fetchall()]
        if emails:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Найденные адреса:\n" + "\n".join(emails))
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Адреса не найдены.")
    except psycopg2.Error as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка при получении данных из базы данных: {e}")

async def get_phone_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cur.execute("SELECT phone_number FROM phone_numbers;")
        phone_numbers = [row[0] for row in cur.fetchall()]
        if phone_numbers:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Найденные номера:\n" + "\n".join(phone_numbers))
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Номера не найдены.")
    except psycopg2.Error as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка при получении данных из базы данных: {e}")

#end
def main():
    def error_handler(update, context):
        print(f"Ошибка: {context.error}")

    application = ApplicationBuilder().token(TOKEN).build()

    find_email_handler = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email)],
        states={
            1: [MessageHandler(filters.TEXT, find_email_text)],
            2: [MessageHandler(filters.TEXT, save_email_db)]
        },
        fallbacks=[]
    )

    find_phone_number_handler = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_number)],
        states={
            1: [MessageHandler(filters.TEXT, find_phone_number_text)],
            2: [MessageHandler(filters.TEXT, save_phone_db)]
        },
        fallbacks=[]
    )
    verify_password_handler = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password)],
        states={
            1: [MessageHandler(filters.TEXT, verify_password_text)]
        },
        fallbacks=[]
    )
    get_apt_list_handler = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list)],
        states={
            1: [MessageHandler(filters.TEXT, get_apt_list_text)]
        },
        fallbacks=[]
    )

    application.add_handler(find_email_handler)
    application.add_handler(find_phone_number_handler)
    application.add_handler(verify_password_handler)
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('get_release', get_release))
    application.add_handler(CommandHandler('get_uptime', get_uptime))
    application.add_handler(CommandHandler('get_df', get_df))
    application.add_handler(CommandHandler('get_free', get_free))
    application.add_handler(CommandHandler('get_mpstat', get_mpstat))
    application.add_handler(CommandHandler('get_w', get_w))
    application.add_handler(CommandHandler('get_auths', get_auths))
    application.add_handler(CommandHandler('get_critical', get_critical))
    application.add_handler(CommandHandler('get_ps', get_ps))
    application.add_handler(CommandHandler('get_ss', get_ss))
    application.add_handler(CommandHandler('get_uname', get_uname))
    application.add_handler(get_apt_list_handler)
    application.add_handler(CommandHandler('get_services', get_services))
    application.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    application.add_handler(CommandHandler('get_emails', get_emails))
    application.add_handler(CommandHandler('get_phone_numbers', get_phone_numbers))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == '__main__':
    main() 
