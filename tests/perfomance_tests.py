import sys
import os
import asyncio
import time
from statistics import mean
import psutil
import logging
from datetime import datetime
import aiohttp
import random
from aiogram import Bot, types
from aiogram.types import Message

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import API_TOKEN
from core.database import Session, User, Work, Review

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotLoadTest:
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'response_times': [],
            'requests_per_minute': [],
            'concurrent_users': set()
        }
        self.test_commands = [
            '/start',
            '/works_list',
            '/read',
            '/read_work',
            '/submit_work'
        ]
        self.test_messages = [
            "Привет, бот!",
            "Как дела?",
            "Хочу почитать",
            "Покажи мои работы",
            "Помощь"
        ]

    async def simulate_message(self, user_id: int):
        """Симуляция отправки сообщения боту"""
        message_text = random.choice(self.test_messages + self.test_commands)
        
        # Создаем объект сообщения
        message = types.Message(
            message_id=random.randint(1, 1000),
            date=datetime.now(),
            chat=types.Chat(
                id=user_id,
                type='private'
            ),
            from_user=types.User(
                id=user_id,
                is_bot=False,
                first_name=f"Test User {user_id}"
            ),
            text=message_text,
            bot=Bot(token=API_TOKEN)
        )

        return message

    async def simulate_user_interaction(self, user_id: int):
        """Симуляция взаимодействия пользователя с ботом"""
        start_time = time.time()
        try:
            # Создаем тестовое сообщение
            message = await self.simulate_message(user_id)
            logger.info(f"User {user_id} sends: {message.text}")

            # Имитируем обработку сообщения ботом
            await asyncio.sleep(random.uniform(0.1, 0.5))  # Имитация времени обработки

            self.metrics['requests_success'] += 1
            self.metrics['response_times'].append(time.time() - start_time)
            self.metrics['concurrent_users'].add(user_id)
            
        except Exception as e:
            logger.error(f"Interaction error for user {user_id}: {e}")
            self.metrics['requests_failed'] += 1

    async def run_load_test(self, num_users: int = 10, duration: int = 60):
        """Запуск нагрузочного тестирования"""
        logger.info(f"Starting load test with {num_users} users for {duration} seconds")
        
        start_time = time.time()
        minute_requests = 0
        last_minute = start_time

        # Создаем пул тестовых пользователей
        test_users = list(range(1, num_users + 1))

        while time.time() - start_time < duration:
            # Выбираем случайное количество активных пользователей
            active_users = random.randint(1, min(5, num_users))
            selected_users = random.sample(test_users, active_users)
            
            # Создаем задачи для каждого активного пользователя
            tasks = [self.simulate_user_interaction(user_id) for user_id in selected_users]
            await asyncio.gather(*tasks)
            
            minute_requests += len(tasks)

            # Подсчет запросов в минуту
            current_time = time.time()
            if current_time - last_minute >= 60:
                self.metrics['requests_per_minute'].append(minute_requests)
                logger.info(f"Requests in last minute: {minute_requests}")
                minute_requests = 0
                last_minute = current_time

            # Пауза между батчами запросов
            await asyncio.sleep(0.5)

        # Формируем результаты
        total_time = time.time() - start_time
        total_requests = self.metrics['requests_success'] + self.metrics['requests_failed']
        
        results = {
            'test_duration': f"{total_time:.2f} seconds",
            'total_requests': total_requests,
            'successful_requests': self.metrics['requests_success'],
            'failed_requests': self.metrics['requests_failed'],
            'concurrent_users_max': len(self.metrics['concurrent_users']),
            'requests_per_minute_avg': (total_requests / (total_time / 60)),
            'success_rate': (self.metrics['requests_success'] / total_requests * 100) if total_requests > 0 else 0,
            'average_response_time': mean(self.metrics['response_times']) if self.metrics['response_times'] else 0
        }

        # Выводим подробный отчет
        logger.info("\nLoad Test Results:")
        for key, value in results.items():
            if isinstance(value, float):
                logger.info(f"{key}: {value:.2f}")
            else:
                logger.info(f"{key}: {value}")

        return results

async def run_tests():
    """Запуск всех тестов"""
    test = BotLoadTest()
    try:
        # Тест с разным количеством пользователей
        for num_users in [5, 10, 20]:
            logger.info(f"\nTesting with {num_users} users...")
            results = await test.run_load_test(num_users=num_users, duration=30)
            
    except Exception as e:
        logger.error(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
