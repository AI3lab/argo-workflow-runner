import tweepy
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

class TwitterClient:
    def __init__(self, api_key: str, api_secret: str):
        """
        初始化 Twitter 客户端
        
        Args:
            api_key (str): Twitter API Key
            api_secret (str): Twitter API Key Secret
        """
        # 设置认证
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret
        )
        
        # 保存认证信息
        self.api_key = api_key
        self.api_secret = api_secret
        
    def get_mentions(self, max_results: int = 100) -> List[Dict]:
        """
        获取提及(@)当前用户的推文
        
        Args:
            max_results (int): 返回结果数量上限
            
        Returns:
            List[Dict]: 提及推文列表
        """
        try:
            # 获取用户提及
            mentions = self.client.get_users_mentions(
                id=self.client.get_me().data.id,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'conversation_id', 'text'],
                user_fields=['name', 'username', 'description', 'profile_image_url'],
                expansions=['author_id']
            )
            
            # 处理结果
            results = []
            if mentions.data:
                # 创建用户信息映射
                users = {user.id: user for user in mentions.includes['users']} if mentions.includes else {}
                
                # 整合推文和用户信息
                for tweet in mentions.data:
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'author': {
                            'id': tweet.author_id,
                            'username': users[tweet.author_id].username if tweet.author_id in users else None,
                            'name': users[tweet.author_id].name if tweet.author_id in users else None,
                            'description': users[tweet.author_id].description if tweet.author_id in users else None,
                            'profile_image_url': users[tweet.author_id].profile_image_url if tweet.author_id in users else None
                        }
                    }
                    results.append(tweet_data)
                    
            return results
            
        except Exception as e:
            print(f"Error getting mentions: {str(e)}")
            return []
            
    def get_user_details(self, usernames: List[str]) -> List[Dict]:
        """
        获取用户详细信息
        
        Args:
            usernames (List[str]): 用户名列表
            
        Returns:
            List[Dict]: 用户信息列表
        """
        try:
            # 获取用户信息
            users = self.client.get_users(
                usernames=usernames,
                user_fields=['name', 'username', 'description', 'profile_image_url', 'public_metrics']
            )
            
            # 处理结果
            results = []
            if users.data:
                for user in users.data:
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'name': user.name,
                        'description': user.description,
                        'profile_image_url': user.profile_image_url,
                        'metrics': user.public_metrics if hasattr(user, 'public_metrics') else None
                    }
                    results.append(user_data)
                    
            return results
            
        except Exception as e:
            print(f"Error getting user details: {str(e)}")
            return []

def main():
    # Twitter API 认证信息
    API_KEY = "0zh2fFPtbndjfmfGrfux2vcC8"
    API_SECRET = "hvR6oWm9ZeQixHbUgtzSizgZWzMEGsP39GBSUwBjLNrUla3Dkw"
    
    # 创建 Twitter 客户端
    client = TwitterClient(API_KEY, API_SECRET)
    
    try:
        # 获取最近的提及
        print("\n=== 获取最近提及 ===")
        mentions = client.get_mentions(max_results=10)
        
        # 打印提及信息
        for mention in mentions:
            print(f"\n推文 ID: {mention['id']}")
            print(f"内容: {mention['text']}")
            print(f"创建时间: {mention['created_at']}")
            print(f"作者: @{mention['author']['username']} ({mention['author']['name']})")
            
        # 获取特定用户的详细信息
        if mentions:
            usernames = [mention['author']['username'] for mention in mentions]
            print("\n=== 获取用户详细信息 ===")
            user_details = client.get_user_details(usernames)
            
            for user in user_details:
                print(f"\n用户名: @{user['username']}")
                print(f"昵称: {user['name']}")
                print(f"简介: {user['description']}")
                if user['metrics']:
                    print(f"关注者数: {user['metrics']['followers_count']}")
                    print(f"关注数: {user['metrics']['following_count']}")
                
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()