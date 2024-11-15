CREATE TABLE IF NOT EXISTS "user" (
	id SERIAL NOT NULL,
	username VARCHAR(256) NOT NULL,
	hashed_password VARCHAR(256) NOT NULL,
	login VARCHAR(256) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT id PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS "package" (
	package_id serial NOT NULL,
    user_id INT REFERENCES "user" (id) ON DELETE CASCADE,
	weight INT NOT NULL,
	length INT NOT NULL,
	width INT NOT NULL,
	height INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT package_id PRIMARY KEY (package_id)
);

-- CREATE TABLE IF NOT EXISTS "delivery" (
-- 	delivery_id serial NOT NULL,
--     package_id INT REFERENCES "package" (package_id) ON DELETE CASCADE,
-- 	recipient_id INT REFERENCES "user" (id) ON DELETE CASCADE,
-- 	sender_id INT REFERENCES "user" (id) ON DELETE CASCADE,
-- 	status VARCHAR(256) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
-- 	CONSTRAINT delivery_id PRIMARY KEY (delivery_id)
-- );