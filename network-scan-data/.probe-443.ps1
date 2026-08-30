$CRLF = [char]13 + [char]10
$c = New-Object Net.Sockets.TcpClient
$c.ReceiveTimeout = 3000
$c.SendTimeout = 3000
try {
  $c.Connect('192.168.0.1', 443)
  $s = $c.GetStream()
  Start-Sleep -Milliseconds 1200
  $buf = New-Object byte[] 512
  if ($s.DataAvailable) {
    $n = $s.Read($buf, 0, 512)
    [Text.Encoding]::ASCII.GetString($buf, 0, $n) -replace '[^\x20-\x7E]', '.'
  } else { '<silent>' }
  $c.Close()
} catch { '<error>' }