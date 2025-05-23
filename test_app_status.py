#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si la aplicación Flask está funcionando
"""

import requests
import time

def test_app_status():
    try:
        response = requests.get('http://127.0.0.1:5000', timeout=5)
        print(f"✅ App está funcionando! Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ App no está respondiendo - puede estar iniciando o detenida")
        return False
    except Exception as e:
        print(f"❌ Error probando la app: {e}")
        return False

if __name__ == '__main__':
    print("Verificando estado de la aplicación...")
    test_app_status() 