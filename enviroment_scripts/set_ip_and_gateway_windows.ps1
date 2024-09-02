$net_data = Get-NetAdapter | Where-Object {{ $_.Name -eq "{interface_name}" }} | Select-Object -Property Name, InterfaceIndex
Remove-NetIPAddress -InterfaceIndex $($net_data.InterfaceIndex) -Confirm:$false
Remove-NetRoute -Confirm:$false
New-NetIPAddress -InterfaceIndex $($net_data.InterfaceIndex) -IPAddress {ip_address} -PrefixLength 24 -DefaultGateway {gateway}
