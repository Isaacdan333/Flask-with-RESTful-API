create DATABASE temp_table;
USE temp_table;
CREATE table user_list (
id int(11) not null auto_increment,
username varchar (50) NOT NULL,
password varchar(255) NOT NULL,
primary key (id)
) auto_increment = 1;