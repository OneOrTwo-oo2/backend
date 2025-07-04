#!/bin/bash

# 원하는 루트 비밀번호 설정
source .env

echo "✅ MariaDB 설치 시작"

# 1. 설치
sudo apt update
sudo apt install -y mariadb-server mariadb-client

# 2. 서비스 시작
sudo service mysql start

# 3. 루트 비밀번호 설정 및 보안 설정
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_PASSWORD}'; FLUSH PRIVILEGES;"
sudo mysql -uroot -p${DB_PASSWORD} -e "DELETE FROM mysql.user WHERE User='';"
sudo mysql -uroot -p${DB_PASSWORD} -e "DROP DATABASE IF EXISTS test;"
sudo mysql -uroot -p${DB_PASSWORD} -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
sudo mysql -uroot -p${DB_PASSWORD} -e "FLUSH PRIVILEGES;"

# 4. user_db 생성
sudo mysql -uroot -p${DB_PASSWORD} -e "CREATE DATABASE IF NOT EXISTS user_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 5. MariaDB 상태 확인
echo "📌 MariaDB 버전:"
sudo mysql -uroot -p${DB_PASSWORD} -e "SELECT VERSION();"

echo "✅ 모든 설정 완료! 'user_db' 데이터베이스가 생성되었습니다."
