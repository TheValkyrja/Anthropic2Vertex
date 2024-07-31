# 转移提示

本项目已恢复继续维护。

本项目的所有核心功能和新功能都将在不改变所有原有功能和用法的情况下在本人新项目进行优先开发，使用原生httpx客户端请求实现，对于从Python启动应用的用户可无缝转移。
请使用python启动的用户移步至新项目测试：https://github.com/TheValkyrja/VertexClaudeProxy

# Anthropic2Vertex
使用官方SDK实现的将标准Anthropic Claude请求转发至VertexAI Claude的代理服务器应用，使用Fastapi。
支持Claude 3.5 sonnet, Claude 3 Opus/Sonnet/Haiku on Vertex AI

## 这个项目是做什么的？
这个项目在本地架设Fastapi服务器，将发送至此服务器的标准Anthropic请求处理模型名后使用官方Anthropic SDK将请求转发至Vertex AI Claude。

### Usage
#### 准备工作：
1.一个已启用结算账号或存在可用额度的GCP账号，且已启用Vertex AI API。（本步骤不提供教程）  
2.一个GCP VertexAI服务账号。  
3.一台可访问对应地区GCP资源的主机。  
4.Docker&Docker Compose或Python运行环境或glibc运行库。（基于你的安装方式及系统）


#### 开始使用

##### 1. 必要前置条件：为GCP账号启用Vertex AI User用于验证：

<details>
  <summary>点击展开</summary>

**为避免不必要的安全性问题，本应用强烈建议使用服务账号限制应用和服务器对GCP的访问。**

1.点击GCP左上角Google图标，点击左上角导航栏，导航至IAM管理-服务账号
![F $O }NYM{J`{C0{90L){2J](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/e6a57671-dad8-4b7a-9dfd-20d62d7a35a3)  

2.创建服务账号  
![)E 7@C_U2{90I2VJUKM}FD](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/469d8314-cdc8-4d48-9299-9505d1fde7eb)

3.随意填写名字和ID，创建，搜索并为其选择Vertex AI User角色,完成创建。
![7(E GI8MUJNT `K CZTN15](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/c179b76d-7e04-4e43-90f2-bd789287bfcc)
![VR33I92N0Z0AANG 0T~)EGW](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/a561ce41-9aaa-417b-9d39-1312875e35fd)

4.点击右侧管理密钥。
![$ _7K@S1CN`O DYLC6HS$X](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/f38c9436-466a-42fe-b69b-fb80c1aabd46)

5.添加密钥-创建密钥-创建。
![` 8}9{$AO~Q5S1P$G3 PU4X](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/572b3e46-47ac-4201-a320-1fbfeacc3e93)

6.浏览器将会自动下载一个密钥文件，你不需要编辑它，只需要妥善保存。

**请像保护密码一样妥善保管此文件！！**

一旦遗失，无法重新下载，泄露将产生严重安全问题。
</details>

##### 2.下载、解压文件。  

<details> 
  <summary>点击展开</summary>
  
**For Linux：**

  ```
  wget --no-check-certificate --content-disposition "https://github.com/TheValkyrja/Anthropic2Vertex/releases/latest/download/Anthropic2Vertex-linux-$(uname -m).tar.gz"
  tar -xzvf Anthropic2Vertex-linux-$(uname -m).tar.gz
  ```
  ```
  sudo rm -rf Anthropic2Vertex-linux-$(uname -m).tar.gz #删除压缩包，可选
  ```

**For Windows:**  

前往[Release](https://github.com/TheValkyrja/Anthropic2Vertex/releases),下载[Anthropic2Vertex.zip](https://github.com/TheValkyrja/Anthropic2Vertex/releases/latest/download/Anthropic2Vertex-windows-x86_64.zip)  
并解压文件。

</details>

##### 3.配置文件。  

<details>
  <summary>点击展开</summary>

导航至解压的文件夹。  

重命名.env.example为.env，并使用文本编辑器编辑.env文件：

将端口，监听地址修改为你的服务器监听地址（默认127.0.0.1:5000）  
并依照需求设置密码（为空即不认证，慎选）。

PROJECT ID可以在GCP首页找到，设置为你自己的ProjectID.
![UZOJG8RSZ HJSFKEU01DJO9](https://github.com/TheValkyrja/Anthropic2Vertex/assets/45366459/f027c76f-b6dd-43eb-96c9-1ffe629de509)

访问区域填写为为你有权访问、且Claude on Vertex正常服务的地区，默认us-east5。

最后，将第一步中下载下来的xxxxxxxxxx.json密钥文件重命名为auth.json，放入文件夹下auth目录中。

</details>

##### 4.安装并启动

<details>
  <summary>从Docker部署启动(推荐)</summary>
  
  本方法的优点：  
  1. 跨平台兼容性强  
  2. 环境隔离  
  3. 避免管理依赖，操作便捷  

  本方法的缺点：
  1. 需要docker环境  
  2. docker框架与镜像总占用空间偏大。

不包括docker框架，本应用镜像文件约占47.2MB（于Ubuntu22.04上本地构建）。

1. 根据你的平台安装对应docker和docker compose

2. 导航至文件夹

3. 启动应用
   运行
   ```
   docker compose up -d
   ```
   启动应用。

   这一指令会在后台将服务运行于你前面设置的地址和端口（默认127.0.0.1:5000）
   以酒馆为例，若你的服务与酒馆运行于同一主机，选择Claude聊天补全，并在代理服务器填入http://127.0.0.1:5000/v1  
   并将密码设置为你配置中的密码并测试连接。

   根据不同前端面板和应用需求设置各异，请自行调整。

安装完成，开始使用。

修改配置后，使用
```
docker compose down
docker compose up -d
```
重新加载配置。

4. （可选）删除目录下main与main.exe文件进一步节省空间。  
   注：照做这步后将无法使用二进制文件启动。确保你知道你在做什么，否则请无视。

</details>

<details>
  
  <summary>直接运行可执行文件（无需前置依赖）</summary>
  
  本方法的优点：  
  1. 无需（也非常不便于）管理任何依赖  
  2. 综合运行体积最优  
  3. 配置运行流程简单  

  本方法的缺点：
  1. 系统兼容性较差（旧版系统可能无法运行）。
  2. 打包应用封闭，内容不透明  
  3. 几乎不存在可调试空间

二进制文件编译于 Debian GNU/Linux 11 (bullseye)与Windows 10 专业版	22H2。任何比这两者更旧或GLIBC不兼容的系统均不保证正常运行。已于Ubuntu22.04进行测试。

**二进制文件内容不透明，因此对你的系统存在安全性风险。  
*USE AT YOUR OWN RISKS***

Pyinstaller SPEC打包文件已提供于源码中。

1. 导航至文件目录。  

2. 启动应用。
      
   For Windows：  

   运行main.exe文件启动应用。
   
   For Linux：
   ```
   #赋予文件运行权限
   chmod +x main
   ./main
   ```

使用方式同上。

</details>

<details>
  
  <summary>使用Python运行</summary>
  
  本方法的优点：  
  1. 所需应用文件体积极小  
  2. 可扩展性与自定义性强  
  3. 代码运行内容安全透明  

  本方法的缺点：
  1. 需要Python运行环境（最好是python3）与Pip包管理器
  2. python依赖与运行库可能占用空间较大。
  3. 对于不同系统兼容性不定。

**如果你看不懂这些内容在说什么，请返回尝试前两种运行方法！**

1. 确保你的系统已经安装了python3与pip3包管理器  
以Ubuntu为例：  
安装python与pip
```
sudo apt-get update
sudo apt install python3 python3-pip
```

2. 安装依赖。  
导航至应用文件夹，运行
```
pip install -r requirements.txt
```

3. 运行。
```
python3 main.py
```
注：对于windows，你可能希望使用```python```替代```python3```。

4. 删除目录下main与main.exe文件进一步节省空间。  
注：照做这步后将无法使用二进制文件启动。确保你知道你在做什么，否则请无视。

应用将会监听于.env文件中设置的对应地址与端口，使用方式与docker运行一样。

</details>

##### 5.进阶配置（多项目负载均衡、控制台输出）

<details> 
  <summary>点击展开</summary>
  
**多项目负载均衡**

本项目已支持使用复数项目ID实现账号负载均衡。  
当auth文件夹内存在auth.json的情况下，应用将以单项目模式启动，始终使用第一个项目+配置文件进行验证。

若要启用多账号模式：

1. 将每个服务账号的验证json文件重命名为其对应访问的项目名.json
例：example-project-123456.json; another-instance-987654.json
并将它们全部放置于auth文件夹下。

2. 在.env文件中，填入你希望启用的项目名，不同项目之间使用后面带一个空格的逗号进行分隔。
例：
```
PROJECT_ID=example-project-123456, another-instance-987654
```

3. 正常启动应用。

如果你设置正确的话，应用会通过动态加权算法，均衡地随机将请求发送至不同项目。
确保你的auth文件夹下没有名称为auth.json的文件，以免应用自动以单账号模式启动。

**控制台调试输出**

本项目已经添加了调试开关。  
在.env中，将```DEBUG```设置为```True```。

应用将会在每一次请求时，实时打印：收到的请求，动态选择器的权重，远端实时回应等信息。

</details>
