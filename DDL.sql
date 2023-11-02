-- Create Organization Table
CREATE TABLE Organization (
    OrganizationID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    ContactInformation VARCHAR(255) NOT NULL,
    Description TEXT,
    Location VARCHAR(255) NOT NULL
);
-- Create User Table
CREATE TABLE User (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Email VARCHAR(255) UNIQUE NOT NULL,
    Role ENUM('voter', 'representative') NOT NULL,
    Password VARCHAR(255) NOT NULL,
    OrganizationID INT,
    FOREIGN KEY (OrganizationID) REFERENCES Organization(OrganizationID)
);



-- Create Post Table (Parent Entity for Issues and Projects)
CREATE TABLE Post (
    PostID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    Description TEXT,
    CreatedAtDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'in progress',
    Topic ENUM('environment', 'social','governance') NOT NULL,
    UserID INT,
    Upvotes INT,
    Downvotes INT,
    OrganizationID INT DEFAULT NULL,
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    FOREIGN KEY (OrganizationID) REFERENCES Organization(OrganizationID)
);

-- Create Comment Table
CREATE TABLE Comment (
    CommentID INT AUTO_INCREMENT PRIMARY KEY,
    Content TEXT,
    CreatedAtDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UserID INT,
    PostID INT,
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    FOREIGN KEY (PostID) REFERENCES Post(PostID)
);

-- Create Sentiment Analysis Table
CREATE TABLE SentimentAnalysis (
    CommentID INT PRIMARY KEY,
    Sentiment VARCHAR(20),
    Confidence FLOAT,
    AnalysisDate TIMESTAMP,
    FOREIGN KEY (CommentID) REFERENCES Comment(CommentID)
);
