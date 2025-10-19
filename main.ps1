param(
    [string]$type,
    [string]$plaintext,
    [string]$key
)


class DragonCipher {
    # 动态S盒生成
    static [byte[]] GenerateDynamicSBox([string]$key) {
        $sbox = 0..255 | ForEach-Object { [byte]$_ }
        $keyBytes = [System.Text.Encoding]::UTF8.GetBytes($key)
        $j = 0
        
        for ($i = 0; $i -lt 256; $i++) {
            $j = ($j + $sbox[$i] + $keyBytes[$i % $keyBytes.Length]) % 256
            $temp = $sbox[$i]
            $sbox[$i] = $sbox[$j]
            $sbox[$j] = $temp
        }
        return $sbox
    }
    
    # 逆S盒生成
    static [byte[]] GenerateInverseSBox([byte[]]$sbox) {
        $inverseSbox = New-Object byte[] 256
        for ($i = 0; $i -lt 256; $i++) {
            $inverseSbox[$sbox[$i]] = $i
        }
        return $inverseSbox
    }
    
    # 修复的龙形螺旋置换
    static [byte[]] DragonSpiralPermutation([byte[]]$data, [string]$key, [bool]$encrypt) {
        $length = $data.Length
        if ($length -eq 0) { return $data }
        
        $result = [byte[]]::new($length)
        $keyBytes = [System.Text.Encoding]::UTF8.GetBytes($key)
        
        # 创建螺旋路径
        $spiralPath = [System.Collections.Generic.List[int]]::new()
        
        # 计算矩阵尺寸
        $size = [Math]::Ceiling([Math]::Sqrt($length))
        $totalSize = $size * $size
        
        # 初始化矩阵，用-1标记空位
        $matrix = @()
        for ($i = 0; $i -lt $totalSize; $i++) {
            $matrix += -1
        }
        
        # 填充数据索引
        $index = 0
        for ($i = 0; $i -lt $totalSize -and $index -lt $length; $i++) {
            $matrix[$i] = $index
            $index++
        }
        
        # 生成螺旋路径
        $top = 0
        $bottom = $size - 1
        $left = 0
        $right = $size - 1
        $direction = 0  # 0:右, 1:下, 2:左, 3:上
        
        while ($top -le $bottom -and $left -le $right) {
            if ($direction -eq 0) {
                # 向右
                for ($i = $left; $i -le $right; $i++) {
                    $pos = $top * $size + $i
                    if ($matrix[$pos] -ne -1) {
                        $spiralPath.Add($matrix[$pos])
                    }
                }
                $top++
            } elseif ($direction -eq 1) {
                # 向下
                for ($i = $top; $i -le $bottom; $i++) {
                    $pos = $i * $size + $right
                    if ($matrix[$pos] -ne -1) {
                        $spiralPath.Add($matrix[$pos])
                    }
                }
                $right--
            } elseif ($direction -eq 2) {
                # 向左
                for ($i = $right; $i -ge $left; $i--) {
                    $pos = $bottom * $size + $i
                    if ($matrix[$pos] -ne -1) {
                        $spiralPath.Add($matrix[$pos])
                    }
                }
                $bottom--
            } elseif ($direction -eq 3) {
                # 向上
                for ($i = $bottom; $i -ge $top; $i--) {
                    $pos = $i * $size + $left
                    if ($matrix[$pos] -ne -1) {
                        $spiralPath.Add($matrix[$pos])
                    }
                }
                $left++
            }
            
            $direction = ($direction + 1) % 4
        }
        
        # 应用置换
        if ($encrypt) {
            # 加密：按螺旋路径重新排列
            for ($i = 0; $i -lt $length; $i++) {
                $result[$i] = $data[$spiralPath[$i]]
            }
        } else {
            # 解密：逆向螺旋路径
            for ($i = 0; $i -lt $length; $i++) {
                $result[$spiralPath[$i]] = $data[$i]
            }
        }
        
        return $result
    }
    
    # 改进的可逆扩散函数
    static [byte[]] DragonDiffusion([byte[]]$data, [string]$key, [bool]$encrypt) {
        $length = $data.Length
        $result = [byte[]]::new($length)
        $keyBytes = [System.Text.Encoding]::UTF8.GetBytes($key)
        
        if ($encrypt) {
            # 加密：前向扩散
            $prev = 0
            for ($i = 0; $i -lt $length; $i++) {
                $keyByte = $keyBytes[$i % $keyBytes.Length]
                $result[$i] = ($data[$i] + $keyByte + $prev + $i) % 256
                $prev = $result[$i]
            }
        } else {
            # 解密：逆向扩散
            $prev = 0
            for ($i = 0; $i -lt $length; $i++) {
                $keyByte = $keyBytes[$i % $keyBytes.Length]
                $original = ($data[$i] - $keyByte - $prev - $i) % 256
                if ($original -lt 0) { $original += 256 }
                $result[$i] = $original
                $prev = $data[$i]  # 注意：这里使用原始密文值
            }
        }
        
        return $result
    }
}

# 加密函数
function encode {
    param(
        [string]$plaintext,
        [string]$key
    )
    
    if ([string]::IsNullOrEmpty($plaintext)) { return "" }
    if ([string]::IsNullOrEmpty($key)) { throw "密钥不能为空" }
    
    # 转换为字节数组
    $data = [System.Text.Encoding]::UTF8.GetBytes($plaintext)
    
    # 生成动态S盒
    $sbox = [DragonCipher]::GenerateDynamicSBox($key)
    
    # Write-Host "加密前数据长度: $($data.Length)" -ForegroundColor Gray
    
    # 3轮加密
    for ($round = 0; $round -lt 3; $round++) {
        # Write-Host "加密轮次: $($round + 1)" -ForegroundColor Gray
        
        # 1. S盒代换
        for ($i = 0; $i -lt $data.Length; $i++) {
            $data[$i] = $sbox[$data[$i]]
        }
        
        # 2. 龙形扩散
        $data = [DragonCipher]::DragonDiffusion($data, $key, $true)
        
        # 3. 龙形螺旋置换
        $data = [DragonCipher]::DragonSpiralPermutation($data, $key, $true)
    }
    
    # 返回Base64编码的密文
    return [Convert]::ToBase64String($data)
}

# 解密函数
function decode {
    param(
        [string]$ciphertext,
        [string]$key
    )
    
    if ([string]::IsNullOrEmpty($ciphertext)) { return "" }
    if ([string]::IsNullOrEmpty($key)) { throw "密钥不能为空" }
    
    # 从Base64解码
    try {
        $data = [Convert]::FromBase64String($ciphertext)
    } catch {
        throw "无效的Base64密文: $($_.Exception.Message)"
    }
    
    # Write-Host "解密数据长度: $($data.Length)" -ForegroundColor Gray
    
    # 生成动态S盒和逆S盒
    $sbox = [DragonCipher]::GenerateDynamicSBox($key)
    $inverseSbox = [DragonCipher]::GenerateInverseSBox($sbox)
    
    # 3轮解密（逆序操作）
    for ($round = 2; $round -ge 0; $round--) {
        # Write-Host "解密轮次: $($round + 1)" -ForegroundColor Gray
        
        # 1. 逆向龙形螺旋置换
        $data = [DragonCipher]::DragonSpiralPermutation($data, $key, $false)
        
        # 2. 逆向龙形扩散
        $data = [DragonCipher]::DragonDiffusion($data, $key, $false)
        
        # 3. 逆向S盒代换
        for ($i = 0; $i -lt $data.Length; $i++) {
            $data[$i] = $inverseSbox[$data[$i]]
        }
    }
    
    # 返回明文
    return [System.Text.Encoding]::UTF8.GetString($data)
}


$host.UI.RawUI.ForegroundColor = "Green"
Write-Host "欢迎使用龙形混淆加密！"
$host.UI.RawUI.ForegroundColor = "Gray"
write-host ">" -NoNewLine
$host.UI.RawUI.ForegroundColor = "White"
write-host " type?[E/d] " -NoNewLine
$host.UI.RawUI.ForegroundColor = "Gray"
$type = read-host
$host.UI.RawUI.ForegroundColor = "Gray"
write-host ">" -NoNewLine
$host.UI.RawUI.ForegroundColor = "White"
write-host " text? " -NoNewLine
$host.UI.RawUI.ForegroundColor = "Gray"
$plaintext = read-host
$host.UI.RawUI.ForegroundColor = "Gray"
write-host ">" -NoNewLine
$host.UI.RawUI.ForegroundColor = "White"
write-host " key? " -NoNewLine
$host.UI.RawUI.ForegroundColor = "Gray"
$key = read-host

if ($type -eq "e" -or $type -eq "E" -or $type -eq "encode"){
    $encrypted = encode -plaintext $plaintext -key $key
    $host.UI.RawUI.ForegroundColor = "White"
    Write-Host "encoded: " -NoNewLine
    $host.UI.RawUI.ForegroundColor = "Yellow"
    write-host $encrypted
}elseif ($type -eq "d" -or $type -eq "D" -or $type -eq "decode"){
    $decrypted = decode -ciphertext $plaintext -key $key
    $host.UI.RawUI.ForegroundColor = "White"
    Write-Host "decoded: " -NoNewLine
    $host.UI.RawUI.ForegroundColor = "Yellow"
    write-host $decrypted
}else{
    $host.UI.RawUI.ForegroundColor = "Red"
    write-host "Unknow en/de type."
}
$host.UI.RawUI.ForegroundColor = "Gray"
