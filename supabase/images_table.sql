CREATE TABLE images (
    id UUID PRIMARY KEY,
    image_name TEXT,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
