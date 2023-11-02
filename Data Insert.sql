-- Insert into Organization Table
INSERT INTO Organization (Name, ContactInformation, Description, Location) VALUES
    ('Org1', 'Contact1', 'Description1', 'Location1'),
    ('Org2', 'Contact2', 'Description2', 'Location2'),
    ('Org3', 'Contact3', 'Description3', 'Location3'),
    ('Org4', 'Contact4', 'Description4', 'Location4'),
    ('Org5', 'Contact5', 'Description5', 'Location5');

-- Insert into User Table
INSERT INTO User (Name, Email, Role, Password, OrganizationID) VALUES
    ('User1', 'user1@example.com', 'voter', 'password1', NULL),
    ('User2', 'user2@example.com', 'voter', 'password2', NULL),
    ('User3', 'user3@example.com', 'representative', 'password3', 1),
    ('User4', 'user4@example.com', 'voter', 'password4', NULL),
    ('User5', 'user5@example.com', 'representative', 'password5', 2);

-- Insert into Post Table
INSERT INTO Post (Title, Description, Topic, UserID, Upvotes, Downvotes, OrganizationID) VALUES
    ('Post1', 'Description1', 'environment', 1, 10, 2, NULL),
    ('Post2', 'Description2', 'social', 2, 15, 3, NULL),
    ('Post3', 'Description3', 'environment', 3, 5, 1, 1),
    ('Post4', 'Description4', 'governance', 4, 8, 0, NULL),
    ('Post5', 'Description5', 'environment', 5, 12, 4, 2);

-- Insert into Comment Table
INSERT INTO Comment (Content, UserID, PostID) VALUES
    ('Comment1', 1, 1),
    ('Comment2', 2, 1),
    ('Comment3', 3, 2),
    ('Comment4', 4, 4),
    ('Comment5', 5, 5);

-- Insert into Sentiment Analysis Table
INSERT INTO SentimentAnalysis (CommentID, Sentiment, Confidence, AnalysisDate) VALUES
    (1, 'Positive', 0.85, NOW()),
    (2, 'Neutral', 0.65, NOW()),
    (3, 'Positive', 0.72, NOW()),
    (4, 'Negative', 0.78, NOW()),
    (5, 'Positive', 0.88, NOW());
