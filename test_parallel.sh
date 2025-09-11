#!/bin/bash
echo "测试CPU"
time_test() {
    local jobs=$1
    echo "测试 -j $jobs:"
    time (
        for i in $(seq 1 $jobs); do
            (
                # 模拟CPU密集型计算
                python3 -c "
import time
start = time.time()
result = 0
for i in range(10000000):
    result += i * i
print(f'Task completed in {time.time()-start:.2f}s')
" &
            done
            wait
        )
    )
    echo "---"
}

time_test 8
time_test 10
time_test 12
