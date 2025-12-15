# RSpec Testing

> Reference for: Rails Expert
> Load when: Writing specs, testing, RSpec, FactoryBot, test coverage

## RSpec Setup

```ruby
# Gemfile
group :development, :test do
  gem 'rspec-rails'
  gem 'factory_bot_rails'
  gem 'faker'
end

group :test do
  gem 'shoulda-matchers'
  gem 'simplecov', require: false
  gem 'capybara'
  gem 'selenium-webdriver'
end

# spec/rails_helper.rb
require 'simplecov'
SimpleCov.start 'rails' do
  add_filter '/spec/'
  add_filter '/config/'
  minimum_coverage 95
end

RSpec.configure do |config|
  config.include FactoryBot::Syntax::Methods

  config.before(:suite) do
    DatabaseCleaner.strategy = :transaction
    DatabaseCleaner.clean_with(:truncation)
  end

  config.around(:each) do |example|
    DatabaseCleaner.cleaning do
      example.run
    end
  end
end

# spec/support/shoulda_matchers.rb
Shoulda::Matchers.configure do |config|
  config.integrate do |with|
    with.test_framework :rspec
    with.library :rails
  end
end
```

## Model Specs

```ruby
# spec/models/user_spec.rb
require 'rails_helper'

RSpec.describe User, type: :model do
  describe "associations" do
    it { should have_many(:posts).dependent(:destroy) }
    it { should have_one(:profile).dependent(:destroy) }
    it { should have_many(:comments) }
  end

  describe "validations" do
    it { should validate_presence_of(:email) }
    it { should validate_uniqueness_of(:email).case_insensitive }
    it { should validate_length_of(:username).is_at_least(3).is_at_most(50) }

    it "validates email format" do
      user = build(:user, email: "invalid")
      expect(user).not_to be_valid
      expect(user.errors[:email]).to include("is invalid")
    end
  end

  describe "callbacks" do
    it "normalizes email before save" do
      user = create(:user, email: "USER@EXAMPLE.COM")
      expect(user.reload.email).to eq("user@example.com")
    end
  end

  describe "#full_name" do
    it "returns first and last name" do
      user = build(:user, first_name: "John", last_name: "Doe")
      expect(user.full_name).to eq("John Doe")
    end
  end

  describe "scopes" do
    let!(:active_user) { create(:user, active: true) }
    let!(:inactive_user) { create(:user, active: false) }

    it "returns only active users" do
      expect(User.active).to include(active_user)
      expect(User.active).not_to include(inactive_user)
    end
  end
end
```

## Request Specs

```ruby
# spec/requests/posts_spec.rb
require 'rails_helper'

RSpec.describe "/posts", type: :request do
  let(:user) { create(:user) }
  let(:valid_attributes) { { title: "Test Post", body: "Content" } }
  let(:invalid_attributes) { { title: "", body: "" } }

  before { sign_in user } # Using Devise helper

  describe "GET /index" do
    it "renders a successful response" do
      create_list(:post, 3)
      get posts_url
      expect(response).to be_successful
    end
  end

  describe "GET /show" do
    it "renders a successful response" do
      post = create(:post)
      get post_url(post)
      expect(response).to be_successful
    end
  end

  describe "POST /create" do
    context "with valid parameters" do
      it "creates a new Post" do
        expect {
          post posts_url, params: { post: valid_attributes }
        }.to change(Post, :count).by(1)
      end

      it "redirects to the created post" do
        post posts_url, params: { post: valid_attributes }
        expect(response).to redirect_to(post_url(Post.last))
      end
    end

    context "with invalid parameters" do
      it "does not create a new Post" do
        expect {
          post posts_url, params: { post: invalid_attributes }
        }.not_to change(Post, :count)
      end

      it "renders unprocessable entity response" do
        post posts_url, params: { post: invalid_attributes }
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe "PATCH /update" do
    let(:post_record) { create(:post, user: user) }
    let(:new_attributes) { { title: "Updated Title" } }

    it "updates the requested post" do
      patch post_url(post_record), params: { post: new_attributes }
      post_record.reload
      expect(post_record.title).to eq("Updated Title")
    end

    it "redirects to the post" do
      patch post_url(post_record), params: { post: new_attributes }
      expect(response).to redirect_to(post_url(post_record))
    end
  end

  describe "DELETE /destroy" do
    it "destroys the requested post" do
      post_record = create(:post, user: user)
      expect {
        delete post_url(post_record)
      }.to change(Post, :count).by(-1)
    end
  end
end
```

## System Specs (Feature Tests)

```ruby
# spec/system/posts_spec.rb
require 'rails_helper'

RSpec.describe "Posts", type: :system do
  before do
    driven_by(:selenium_chrome_headless)
  end

  let(:user) { create(:user) }

  describe "creating a post" do
    it "allows user to create a new post" do
      sign_in user
      visit new_post_path

      fill_in "Title", with: "My New Post"
      fill_in "Body", with: "This is the content"
      click_button "Create Post"

      expect(page).to have_content("Post was successfully created")
      expect(page).to have_content("My New Post")
    end
  end

  describe "editing a post", js: true do
    it "updates post via Turbo Frame" do
      post = create(:post, user: user)
      sign_in user
      visit post_path(post)

      click_link "Edit"
      fill_in "Title", with: "Updated Title"
      click_button "Update Post"

      expect(page).to have_content("Updated Title")
      expect(page).not_to have_selector("form")
    end
  end
end
```

## FactoryBot

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email { Faker::Internet.email }
    username { Faker::Internet.username(specifier: 3..50) }
    password { "Password123!" }

    trait :admin do
      role { :admin }
    end

    trait :with_posts do
      transient do
        posts_count { 3 }
      end

      after(:create) do |user, evaluator|
        create_list(:post, evaluator.posts_count, user: user)
      end
    end
  end

  factory :post do
    title { Faker::Lorem.sentence }
    body { Faker::Lorem.paragraph }
    association :user

    trait :published do
      published { true }
      published_at { Time.current }
    end
  end
end

# Usage
user = create(:user)
admin = create(:user, :admin)
user_with_posts = create(:user, :with_posts, posts_count: 5)
published_post = create(:post, :published)
```

## Shared Examples

```ruby
# spec/support/shared_examples/authenticatable.rb
RSpec.shared_examples "authenticatable" do
  describe "authentication" do
    context "when not signed in" do
      it "redirects to sign in page" do
        make_request
        expect(response).to redirect_to(new_user_session_path)
      end
    end

    context "when signed in" do
      before { sign_in create(:user) }

      it "allows access" do
        make_request
        expect(response).to be_successful
      end
    end
  end
end

# Usage in request spec
RSpec.describe "/admin/posts", type: :request do
  include_examples "authenticatable" do
    let(:make_request) { get admin_posts_path }
  end
end
```

## Testing Jobs

```ruby
# spec/jobs/email_sender_job_spec.rb
require 'rails_helper'

RSpec.describe EmailSenderJob, type: :job do
  describe "#perform" do
    let(:user) { create(:user) }

    it "sends email" do
      expect {
        described_class.perform_now(user.id, :welcome)
      }.to change { ActionMailer::Base.deliveries.count }.by(1)
    end

    it "enqueues job" do
      expect {
        described_class.perform_later(user.id, :welcome)
      }.to have_enqueued_job(described_class)
        .with(user.id, :welcome)
        .on_queue("default")
    end
  end
end
```

## Testing Mailers

```ruby
# spec/mailers/user_mailer_spec.rb
require 'rails_helper'

RSpec.describe UserMailer, type: :mailer do
  describe "welcome_email" do
    let(:user) { create(:user) }
    let(:mail) { UserMailer.welcome_email(user) }

    it "renders the headers" do
      expect(mail.subject).to eq("Welcome to Our App")
      expect(mail.to).to eq([user.email])
      expect(mail.from).to eq(["noreply@example.com"])
    end

    it "renders the body" do
      expect(mail.body.encoded).to match(user.username)
    end
  end
end
```

## Best Practices

- Use `let` and `let!` for DRY specs
- Use factories, not fixtures
- One assertion per example when possible
- Use descriptive test names
- Test edge cases and error conditions
- Keep tests fast (use build instead of create when possible)
- Use `travel_to` for time-dependent tests
- Mock external API calls
