import json
import logging
import uuid

import requests


logging.basicConfig(level=logging.INFO)

headers = {'APS-Token': 'JEFFUy0xMjgtR0NNJDNGNEUxZlBKTDhkWEhqc2MkbzlaaXE3THc5S1JpMENMSmN2L2lsTm4wTVhNRXozK3ZhNm1rWFVOTGRnUm4xd2Y5NzJZS1B3T0duRHVFeHFVVUpHK1pxZlBnSDR1WjVuRzduYzkyeXZDWFpaSktoSDgvVXNZbm9vVWlRelNJNisyMWpiRzQ4TWsxbWE2Q2dteHJZKzJRNjhkQkY4K0VFaHRSN1Qyb09GbFpma2U2UHo5bDU2Mmoza0hrRXhrK1ZQWnpCK2o4VnpGVnA4MVd0Uk80cFhWTHdhRkpkYXA5UTl6T3RZUzFFTFpWMDRwSnIyRmhlSStaUkZEbUlZeTNyWHBqZzB6L0l6L3RqaUI4bG1NOFBEdVJ2d0M1TW11WTZpM0x5KzVHc3JLN0wwS0ZWY2NidDhKWWpZY1gybEkwQWpiaDdTRm04SEFHRjRNbjZhaG42SzA1dTJPT0VjMHdNRThKenZlVytqeTFHREQvbHNwSktxMFpYYVA3ZUg0V1kzei8yRmg3ellpMWt2Z2JkbEhURk9KaDNhQis2VXZOdjRHVEZPekFEK0ZLUWs5bWpSMWlrbkZYRko3OUYyWXZGZ0pWbzA0SHRnck43SklOeVIycENVTHY3YUM3a0lTdGd5WFc5cVlGR1lJazNRem1ZYzdlbEExRGVMRlBMVmY3bjVDM0k4R1YxVExZS1hERDZxdEROKzZ2'}


url = "http://10.26.163.119:8080/aps/2/resources"
r = requests.get(url, headers=headers)

print(r.text)


#curl -H "Content-Type: application/json" -H "APS-Token: JEFFUy0xMjgtR0NNJCtHMzFpdzZ2ckZRbGVCZWwkRkxMUEdiVnpaRXNNQVpya2d3TjNEQko3d2Y2dHJEQm1aV0tnSnhPYVlpUWkvZ1FkUnFSb3NzYnZhdWJIN0p5Q0l1TDdMU014YTBHaHVWamsrZGNvc0JGWnVjanArc3RQQXI0WTJvUDNWSmZpWjRQa0kvYWZyYWhGSWZheG53ay9nb2RucWJZelh1MzBRSFZiV0ZFWHo0OFpzc1A3KzhybVFQRTZNemEwTlo1enU3YzZVZm1BMGpSMzdZbTFJNnpYTTJsUlBqV29FNXhMd2dIZjZVYUpSSXNMZDZLSkxrNUlHcnpBSWgxOVRvemdxaG14U3RyWDMySzFnMTdUU1puTHhnaEN3YmptbHhKblA1NG1pV05jaWswdmwyRTFqTnF6ZUNhNEc3NHVrcXViZTFQblptank1Qno3T0N1N25kbGY5RjNlSHd0RVRXWDlNMmVqWmVZTUhxYXpIR3VGRjJLYUV0WDk0OU95TmtIdjB4bGNwSlpEWkcrOWVTNWxxenNhWEJmdUFEamJUdmg3bFkxdVd5UWx2bVZ2dDNTeERiV0U3ZVUwSURLQld0dmN6WHJFQXd5WUhjT2gwZCtvL1pkZkV4aVhaSnIwTjNpcnl3SVdRTHhiTTJ1MHJzT0FwLzRkekduaXljSFdWeXJXOGtBdmRxdVo2aE4zZGpMamZtNW9aVnFy" --data '{"companyName": "LightProvider", "taxRegistrationId": "", "currencyId": "EUR", "addressLine1": "123", "addressLine2": "", "city": "Moscow", "state": "MOW", "postalCode": "123456", "country": "ru", "firstName": "firstName", "middleName": "123", "lastName": "123", "email": "aaa@test.pa", "phoneCountry": "7", "phoneArea": "999", "phoneNumber": "4444444", "phoneExtension": "", "faxCountry": "7", "faxArea": "999", "faxNumber": "1111111", "faxExtension": "888", "dnsServiceTemplateId": "2", "secret": "secret", "newPassword": "sss", "bvt": "true" }' -X POST http://10.26.163.119:8080/aps/2/resources/5d0cccca-16a8-4b27-b221-2c5aaebe53f8/contact/initialize
