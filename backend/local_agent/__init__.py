"""Corpo local (FASE 5) — a ponte segura entre a Mente Colmeia (remota) e o
dispositivo (local). ABERTURA CAUTELOSA: por enquanto SÓ a trava de segurança
(capability tokens + comandos assinados). Nenhuma I/O de device é executada aqui.

Princípio (cérebro remoto × corpo local): o servidor apenas **propõe** (assina um
grant de capacidade); quem **valida e executa** é o Local Agent nativo, no
dispositivo. O servidor nunca recebe acesso irrestrito à máquina.
"""
