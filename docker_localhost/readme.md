多个项目一起使用docker-compose 管理。
先把别的前端项目打包成docker image。
然后push 到 docker hub。
再修改docker-compose 的server 为 dockerhub 的地址就可以了。