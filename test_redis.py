"""
Test Redis connection for face recognition system
"""
import redis
import sys

def test_redis_connection():
    """Test if Redis server is accessible"""
    print("Testing Redis connection...")
    print("-" * 50)
    
    try:
        # Try to connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test with ping
        response = r.ping()
        
        if response:
            print("✓ Redis connection successful!")
            print(f"  Server: localhost:6379")
            print(f"  Response: PONG")
            
            # Try to get info
            info = r.info()
            print(f"  Redis version: {info.get('redis_version', 'unknown')}")
            print(f"  Used memory: {info.get('used_memory_human', 'unknown')}")
            
            # Check if any users are registered
            known_users = r.scard("known_users")
            print(f"  Registered users: {known_users}")
            
            if known_users > 0:
                users = r.smembers("known_users")
                print("  Users in database:")
                for user in users:
                    user_name = user.decode('utf-8').replace('_', ' ').title()
                    print(f"    - {user_name}")
            
            print("\n✓ Face recognition system ready!")
            return True
            
    except redis.ConnectionError:
        print("✗ Could not connect to Redis server")
        print("\nPlease ensure Redis is running:")
        print("  1. Start Redis server: redis-server")
        print("  2. Or start Redis as a Windows service")
        print("  3. Check if Redis is in your PATH")
        return False
        
    except Exception as e:
        print(f"✗ Error testing Redis: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
