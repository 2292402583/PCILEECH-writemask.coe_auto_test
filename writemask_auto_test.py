# -*- coding: utf-8 -*-
import os
import sys
import time
import codecs
from arbor.modules.ArborDriver import driver
from arbor.domain.ArborDevices import BDF

# 设置默认编码为UTF-8
reload(sys)
sys.setdefaultencoding('utf-8')

# 初始化ARBOR驱动
drv = driver()

# 设备BDF
bdf = BDF(5, 0, 0)#作者梦入神机dtt
#作者梦入神机dtt
#作者梦入神机dtt
#作者梦入神机dtt
#作者梦入神机dtt
#作者梦入神机dtt
#作者梦入神机dtt
#作者梦入神机dtt

# 定义测试范围
start = 0x00  # 起始偏移量
stop = 0xFE0  # 结束偏移量

# 创建文件夹
base_dir = u"C:\\Users\\13263\\PCIe_Test_Results"
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# 读取配置空间
config_space = drv.readConfigSpace(bdf)

# 根据当前时间戳生成文件名
timestamp = time.strftime("%Y%m%d_%H%M%S")
config_coe_filename = os.path.join(base_dir, u"pcileech_cfgspace_%s.coe" % timestamp)
mask_coe_filename = os.path.join(base_dir, u"mask_%s.coe" % timestamp)
mask_txt_filename = os.path.join(base_dir, u"mask_%s.txt" % timestamp)

# 初始化文件内容
with codecs.open(config_coe_filename, 'w', 'utf-8') as config_coe_file, \
        codecs.open(mask_coe_filename, 'w', 'utf-8') as mask_coe_file, \
        codecs.open(mask_txt_filename, 'w', 'utf-8') as mask_txt_file:
    config_coe_file.write(u"memory_initialization_radix=16;\nmemory_initialization_vector=\n")
    mask_coe_file.write(u"memory_initialization_radix=16;\nmemory_initialization_vector=\n")

def convert_to_little_endian(hex_value):
    """ 将32位十六进制值转换为小端序，并转换为小写 """
    hex_str = hex_value.zfill(8).lower()  # 确保每个值为8位并转换为小写
    little_endian = hex_str[6:8] + hex_str[4:6] + hex_str[2:4] + hex_str[0:2]
    return little_endian

sequence_number = 1  # 序号计数器

for offset in range(start, stop + 1, 16):  # 每次处理4个32位寄存器（即16字节）
    coe_values = []
    mask_values = []
    txt_entries = []

    # 显示当前寄存器序号
    print("Processing Register Sequence: %d" % sequence_number)

    # 提示用户是否跳过生成
    user_input = raw_input("按回车继续，输入'N'跳过并填充XXXXXXXX: ").strip().upper()
    if user_input == 'N':
        # 用户选择跳过，填充XXXXXXXX
        for i in range(4):
            coe_values.append("XXXXXXXX")
            mask_values.append("XXXXXXXX")
            txt_entries.append("XXXXXXXX / Offset: 0x%02X-0x%02X 配置空间为：XX XX XX XX\n" % (offset + i*4, offset + i*4 + 3))
    else:
        # 处理4个32位寄存器
        for i in range(4):
            binary_mask = ""
            config_hex_value = ""
            config_space_values = []

            for byte_offset in range(4):
                current_value = config_space[offset + i*4 + byte_offset]
                config_space_values.append("%02x" % current_value)  # 转换为小写
                byte_mask = ""

                for bit_position in range(8):  # 每个寄存器有8个位
                    mask = 1 << bit_position  # 位掩码
                    original_bit_value = (current_value >> bit_position) & 1  # 计算原始位值

                    try:
                        # 尝试将某个位反转并写入
                        new_value = current_value ^ mask
                        drv.writePciConfig(bdf, offset + i*4 + byte_offset, 1, new_value)

                        # 读取写入后的值
                        updated_value = drv.readPciConfig(bdf, offset + i*4 + byte_offset, 1)

                        if updated_value == current_value:
                            byte_mask += '0'
                        else:
                            byte_mask += '1'

                        # 恢复原始值
                        drv.writePciConfig(bdf, offset + i*4 + byte_offset, 1, current_value)

                    except Exception as e:
                        byte_mask += '0'

                # 累积每个字节的掩码和对应的十六进制值
                binary_mask = byte_mask + binary_mask
                config_hex_value = "%02x" % current_value + config_hex_value  # 转换为小写

            # 转换为小端序
            little_endian_value = convert_to_little_endian(config_hex_value)
            config_space_str = " ".join(config_space_values)

            coe_values.append(little_endian_value)
            mask_values.append("%08x" % int(binary_mask, 2))
            txt_entries.append("%s / Offset: 0x%02X-0x%02X 配置空间为：%s\n" % (binary_mask, offset + i*4, offset + i*4 + 3, config_space_str))

    # 将结果写入文件
    with codecs.open(config_coe_filename, 'a', 'utf-8') as config_coe_file:
        config_coe_file.write(",".join(coe_values) + ",\n")

    with codecs.open(mask_coe_filename, 'a', 'utf-8') as mask_coe_file:
        mask_coe_file.write(",".join(mask_values) + ",\n")

    with codecs.open(mask_txt_filename, 'a', 'utf-8') as mask_txt_file:
        mask_txt_file.writelines(txt_entries)

    sequence_number += 1  # 增加序号

print("配置空间COE、MASK COE和MASK TXT文件已成功生成，保存在 %s 目录下。" % base_dir)
