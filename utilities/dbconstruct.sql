CREATE TABLE IF NOT EXISTS t_user_info (

    user_id BIGSERIAL NOT NULL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
	email VARCHAR(50) NOT NULL, 
    first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
    user_password VARCHAR(150) NOT NULL,
	gender VARCHAR(50) NOT NULL,
	date_of_birth VARCHAR(50),
	country_of_birth VARCHAR(50),
    cellphone_number text NOT NULL,
	last_login VARCHAR(50),
    api_key VARCHAR(50),
    api_key_gen_time VARCHAR(50),
    verification_link VARCHAR(150),
    account_active boolean,
    account_verified boolean,
    account_type INT,
    reset_password_token VARCHAR(50),
    profile_pic VARCHAR(50),
    cellphone_code INT,
    cellphone_verified boolean,
    time_offset INT,
    address_line_1 VARCHAR(150),
    address_line_2 VARCHAR(150),
    address_postal_code INT,
    address_state VARCHAR(150),
    address_country VARCHAR(50),
    whatsapp_messages BIGINT,
    sms_messages BIGINT,
    verification_counter BIGINT,
    verification_time BIGINT,
    api_calls BIGINT
);

CREATE TABLE IF NOT EXISTS t_dynamic_interface (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    interface_id BIGINT,
    interface_url text,
    interface_token text ,
    interface_description text,
    table_name text,
    fields JSON[],
    interface_details json,
    update_period bigint,
    last_modified bigint,
    actual_update_time BIGINT,
    notification_sent boolean,
    notification_enabled boolean,
    last_notification_status text,
    whatsapp_enabled boolean,
    sms_enabled boolean,
    notification_users JSONB,
	interface_owner BIGSERIAL REFERENCES t_user_info (user_id)
);

CREATE TABLE IF NOT EXISTS t_session(
    id BIGSERIAL NOT NULL PRIMARY KEY,
    session_id text NOT NULL,
    user_id BIGSERIAL REFERENCES t_user_info (user_id),
    session_ip_address text,
    session_start_time BIGINT,
    session_end_time BIGINT,
    session_duration BIGINT,
    user_agent text,
    device_type text,
    referrer text,
    session_status boolean, 
    session_location text,
    session_error_log text,
    session_data json
);

insert into t_config(config_username, config_password, config_email, smtp_server_address, sender_email_address, smtp_username, smtp_password, smtp_port, domain) 
values ('master','spoilerpswd','admin@xyz.com','mail.xyz.com','no-reply@xyz.com','', ')FL-oFEg6b{z6Ox-', 465, 'https://www.xyz.com');