# oddiy_nginx_test.py - oddiy va tez test
import requests
import time
import random

def oddiy_test():
    server = "http://83.222.16.96"
    
    # API yo'llari
    apis = [
        "/api/v1/login",
        "/api/v1/users",
        "/api/health",
        "/api/test",
        "/v1/ping",
        "/admin",
        "/wp-login.php",
        "/phpmyadmin",
    ]
    
    print("🚀 NGINX oddiy test")
    print(f"Server: {server}")
    print("="*50)
    
    for i in range(100):  # 100 ta so'rov
        api = random.choice(apis)
        fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        try:
            url = f"{server}{api}"
            headers = {'X-Forwarded-For': fake_ip}
            
            response = requests.get(url, headers=headers, timeout=3, verify=False)
            
            if i % 10 == 0:  # Har 10-ta so'rovda ko'rsatish
                print(f"{i+1}/100: {response.status_code} {url}")
            
        except:
            pass
        
        time.sleep(0.05)  # Juda tez so'rovlar
    
    print("\n✅ 100 ta so'rov yuborildi!")
    print("📱 Telegram botdan xabar kelinganini tekshiring")

if __name__ == "__main__":
    oddiy_test()