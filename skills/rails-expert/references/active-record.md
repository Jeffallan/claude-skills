# Active Record Patterns

> Reference for: Rails Expert
> Load when: Models, associations, queries, migrations, performance

## Model Associations

```ruby
# app/models/user.rb
class User < ApplicationRecord
  has_many :posts, dependent: :destroy
  has_many :comments, dependent: :destroy
  has_many :commented_posts, through: :comments, source: :post

  has_one :profile, dependent: :destroy
  has_one_attached :avatar
  has_many_attached :documents

  validates :email, presence: true, uniqueness: true
  validates :username, presence: true, length: { minimum: 3, maximum: 50 }

  before_save :normalize_email

  private

  def normalize_email
    self.email = email.downcase.strip
  end
end

# app/models/post.rb
class Post < ApplicationRecord
  belongs_to :user
  has_many :comments, dependent: :destroy
  has_many :taggings, dependent: :destroy
  has_many :tags, through: :taggings

  scope :published, -> { where(published: true) }
  scope :recent, -> { order(created_at: :desc) }
  scope :by_user, ->(user) { where(user: user) }

  validates :title, presence: true, length: { maximum: 200 }
  validates :body, presence: true
end
```

## Query Optimization

Prevent N+1 queries:

```ruby
# Bad - N+1 query
@posts = Post.all
@posts.each { |post| puts post.user.name }

# Good - eager loading
@posts = Post.includes(:user)
@posts.each { |post| puts post.user.name }

# Multiple associations
@posts = Post.includes(:user, :comments, :tags)

# Nested associations
@posts = Post.includes(comments: :user)

# Use joins when you don't need the associated records
@posts = Post.joins(:user).where(users: { active: true })
```

Query scopes:

```ruby
class Post < ApplicationRecord
  scope :published, -> { where(published: true) }
  scope :recent, ->(limit = 10) { order(created_at: :desc).limit(limit) }
  scope :by_tag, ->(tag) { joins(:tags).where(tags: { name: tag }) }
  scope :search, ->(query) { where("title ILIKE ?", "%#{sanitize_sql_like(query)}%") }

  # Class method for complex logic
  def self.trending(days = 7)
    where("created_at > ?", days.days.ago)
      .joins(:comments)
      .group(:id)
      .order("COUNT(comments.id) DESC")
  end
end

# Usage
Post.published.recent(5)
Post.by_tag("rails").search("hotwire")
```

## Advanced Queries

```ruby
# Select specific columns
Post.select(:id, :title, :created_at)

# Count and group
User.joins(:posts).group(:id).count
User.joins(:posts).group("users.id").select("users.*, COUNT(posts.id) as posts_count")

# Pluck for arrays
User.pluck(:email)
User.pluck(:id, :email) # Returns array of arrays

# Find by SQL
Post.find_by_sql("SELECT * FROM posts WHERE title ILIKE '%rails%'")

# Exists?
Post.where(published: true).exists?

# Batch processing
User.find_each(batch_size: 1000) do |user|
  user.process_something
end
```

## Callbacks

```ruby
class User < ApplicationRecord
  before_validation :normalize_email
  after_validation :log_errors

  before_create :generate_token
  after_create :send_welcome_email

  before_save :update_slug
  after_save :clear_cache

  before_destroy :cleanup_associations
  after_destroy :log_deletion

  # Avoid callbacks for business logic - use service objects instead

  private

  def normalize_email
    self.email = email.downcase.strip if email.present?
  end

  def generate_token
    self.token = SecureRandom.hex(32)
  end
end
```

## Validations

```ruby
class Article < ApplicationRecord
  validates :title, presence: true, length: { minimum: 5, maximum: 200 }
  validates :slug, uniqueness: { case_sensitive: false }
  validates :published_at, comparison: { greater_than: Time.current }, if: :published?

  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :age, numericality: { greater_than_or_equal_to: 18 }

  validate :validate_future_date

  private

  def validate_future_date
    if published_at.present? && published_at < Time.current
      errors.add(:published_at, "must be in the future")
    end
  end
end
```

## Migrations

```ruby
# db/migrate/20231214_create_posts.rb
class CreatePosts < ActiveRecord::Migration[7.1]
  def change
    create_table :posts do |t|
      t.string :title, null: false
      t.text :body, null: false
      t.boolean :published, default: false, null: false
      t.references :user, null: false, foreign_key: true

      t.timestamps
    end

    add_index :posts, :published
    add_index :posts, [:user_id, :created_at]
  end
end

# Adding columns
class AddSlugToPosts < ActiveRecord::Migration[7.1]
  def change
    add_column :posts, :slug, :string
    add_index :posts, :slug, unique: true
  end
end

# Data migration
class BackfillUsernames < ActiveRecord::Migration[7.1]
  def up
    User.where(username: nil).find_each do |user|
      user.update_column(:username, "user_#{user.id}")
    end
  end

  def down
    # Usually not needed for data migrations
  end
end
```

## Concerns

```ruby
# app/models/concerns/sluggable.rb
module Sluggable
  extend ActiveSupport::Concern

  included do
    before_validation :generate_slug
    validates :slug, presence: true, uniqueness: true
  end

  private

  def generate_slug
    self.slug ||= title.parameterize if title.present?
  end
end

# Usage in model
class Post < ApplicationRecord
  include Sluggable
end
```

## Performance Tips

- Add database indexes for frequently queried columns
- Use `counter_cache` for associations
- Use `select` to limit columns returned
- Use `pluck` instead of `map` for single attributes
- Use `find_each` for batch processing large datasets
- Use database views for complex queries
- Consider materialized views for expensive aggregations
