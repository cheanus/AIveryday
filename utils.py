import subprocess

def notify(msg, args):
    if args['notify']['platform'] == 'linux':
        subprocess.run(['notify-send', 
                        '-i', args['notify']['icon_path'],
                        '-a', args['notify']['app_name'],
                        '-t', str(1000*args['notify']['expire_time']),
                        args['notify']['title'], 
                        msg], check=True)
    else:
        from plyer import notification
        notification.notify(
            title=args['notify']['title'],
            message=msg,
            app_name=args['notify']['app_name'],
            timeout=args['notify']['expire_time'],
            app_icon=args['notify']['icon_path']
        )

def get_free_gpu_memory():
    # 运行 nvidia-smi 命令并获取输出
    result = subprocess.run(
        ['nvidia-smi', '--query-gpu=memory.free', '--format=csv,nounits,noheader'],
        stdout=subprocess.PIPE,
        encoding='utf-8'
    )
    
    # 解析输出
    output = result.stdout.strip()
    free_memory = []
    for line in output.split('\n'):
        free = int(line)
        free_memory.append(free)
    
    return max(free_memory)