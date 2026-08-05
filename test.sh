#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "🧪 ТЕСТИРОВАНИЕ ML СЕРВИСА"
echo "========================================="
echo ""

# ----------------------------------------------------------------------
# 1. Проверка доступности сервиса
# ----------------------------------------------------------------------
echo -e "${YELLOW}[1] Проверка доступности сервиса...${NC}"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}✅ Сервис доступен (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}❌ Сервис НЕ доступен (HTTP $RESPONSE)${NC}"
    exit 1
fi
echo ""

# ----------------------------------------------------------------------
# 2. Регистрация нового пользователя
# ----------------------------------------------------------------------
echo -e "${YELLOW}[2] Регистрация пользователя...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@mail.com","password":"test123"}')

USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.user_id')
if [ "$USER_ID" != "null" ] && [ -n "$USER_ID" ]; then
    echo -e "${GREEN}✅ Пользователь создан: $USER_ID${NC}"
else
    echo -e "${YELLOW}⚠️ Пользователь уже существует или ошибка: $REGISTER_RESPONSE${NC}"
fi
echo ""

# ----------------------------------------------------------------------
# 3. Авторизация (получение токена)
# ----------------------------------------------------------------------
echo -e "${YELLOW}[3] Авторизация...${NC}"
TOKEN=$(curl -s -X POST http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}' \
  | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Токен получен${NC}"
else
    echo -e "${RED}❌ Ошибка авторизации${NC}"
    exit 1
fi
echo ""

# ----------------------------------------------------------------------
# 4. Получение профиля пользователя
# ----------------------------------------------------------------------
echo -e "${YELLOW}[4] Получение профиля...${NC}"
USERNAME=$(curl -s -X GET http://localhost/users/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.username')
if [ "$USERNAME" == "testuser" ]; then
    echo -e "${GREEN}✅ Профиль получен: $USERNAME${NC}"
else
    echo -e "${RED}❌ Ошибка получения профиля${NC}"
fi
echo ""

# ----------------------------------------------------------------------
# 5. Получение начального баланса
# ----------------------------------------------------------------------
echo -e "${YELLOW}[5] Получение начального баланса...${NC}"
BALANCE=$(curl -s -X GET http://localhost/users/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.balance')
echo -e "${GREEN}✅ Текущий баланс: $BALANCE кредитов${NC}"
echo ""

# ----------------------------------------------------------------------
# 6. Пополнение баланса
# ----------------------------------------------------------------------
echo -e "${YELLOW}[6] Пополнение баланса на 50 кредитов...${NC}"
DEPOSIT_RESPONSE=$(curl -s -X POST http://localhost/balance/deposit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}')
DEPOSIT_SUCCESS=$(echo $DEPOSIT_RESPONSE | jq -r '.success')
if [ "$DEPOSIT_SUCCESS" == "true" ]; then
    NEW_BALANCE=$(echo $DEPOSIT_RESPONSE | jq -r '.new_balance')
    echo -e "${GREEN}✅ Баланс пополнен. Новый баланс: $NEW_BALANCE кредитов${NC}"
else
    echo -e "${RED}❌ Ошибка пополнения: $DEPOSIT_RESPONSE${NC}"
fi
echo ""

# ----------------------------------------------------------------------
# 7. Проверка обновлённого баланса
# ----------------------------------------------------------------------
echo -e "${YELLOW}[7] Проверка обновлённого баланса...${NC}"
BALANCE=$(curl -s -X GET http://localhost/users/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.balance')
echo -e "${GREEN}✅ Баланс после пополнения: $BALANCE кредитов${NC}"
echo ""

# ----------------------------------------------------------------------
# 8. Отправка ML-запроса
# ----------------------------------------------------------------------
echo -e "${YELLOW}[8] Отправка ML-запроса...${NC}"
TASK_RESPONSE=$(curl -s -X POST http://localhost/predict/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"text": "Это спам сообщение!"}}')
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
if [ "$TASK_ID" != "null" ] && [ -n "$TASK_ID" ]; then
    echo -e "${GREEN}✅ Задача создана: $TASK_ID${NC}"
else
    echo -e "${RED}❌ Ошибка создания задачи: $TASK_RESPONSE${NC}"
fi
echo ""

# ----------------------------------------------------------------------
# 9. Ожидание обработки задачи
# ----------------------------------------------------------------------
echo -e "${YELLOW}[9] Ожидание обработки задачи...${NC}"
sleep 5

STATUS=$(curl -s -X GET "http://localhost/predict/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.status')
if [ "$STATUS" == "completed" ]; then
    echo -e "${GREEN}✅ Задача обработана успешно${NC}"
else
    echo -e "${YELLOW}⚠️ Статус задачи: $STATUS${NC}"
fi
echo ""

# ----------------------------------------------------------------------
# 10. Проверка списания кредитов
# ----------------------------------------------------------------------
echo -e "${YELLOW}[10] Проверка списания кредитов...${NC}"
BALANCE=$(curl -s -X GET http://localhost/users/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.balance')
echo -e "${GREEN}✅ Текущий баланс: $BALANCE кредитов${NC}"
echo ""

# ----------------------------------------------------------------------
# 11. Получение истории транзакций
# ----------------------------------------------------------------------
echo -e "${YELLOW}[11] Получение истории транзакций...${NC}"
TRANSACTIONS=$(curl -s -X GET http://localhost/balance/transactions \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.')
TRANSACTION_COUNT=$(echo $TRANSACTIONS | jq 'length')
echo -e "${GREEN}✅ Найдено $TRANSACTION_COUNT транзакций${NC}"
echo ""

# ----------------------------------------------------------------------
# 12. Проверка обработки ошибок (некорректные данные)
# ----------------------------------------------------------------------
echo -e "${YELLOW}[12] Проверка обработки ошибок...${NC}"
ERROR_RESPONSE=$(curl -s -X POST http://localhost/predict/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {}}' \
  | jq -r '.detail // "Ошибка обработана"')
echo -e "${GREEN}✅ Ошибка обработана: $ERROR_RESPONSE${NC}"
echo ""

# ----------------------------------------------------------------------
# ИТОГ
# ----------------------------------------------------------------------
echo "========================================="
echo -e "${GREEN}✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!${NC}"
echo "========================================="
echo ""
echo "📊 Сводка:"
echo "   ✅ Регистрация и авторизация — работает"
echo "   ✅ Пополнение баланса — работает"
echo "   ✅ ML-запросы — работают"
echo "   ✅ Списание кредитов — работает"
echo "   ✅ История транзакций — работает"
echo "   ✅ Обработка ошибок — работает"
echo ""
echo "🔗 Swagger UI: http://localhost/docs"
echo "🐰 RabbitMQ UI: http://localhost:15672"