# Hotwire & Turbo

> Reference for: Rails Expert
> Load when: Implementing Turbo Frames, Turbo Streams, Stimulus controllers

## Turbo Drive

Turbo Drive automatically converts link clicks and form submissions into AJAX requests:

```ruby
# app/controllers/articles_controller.rb
class ArticlesController < ApplicationController
  def create
    @article = Article.new(article_params)

    if @article.save
      redirect_to @article, notice: "Article created!"
    else
      render :new, status: :unprocessable_entity
    end
  end
end
```

```erb
<!-- app/views/articles/new.html.erb -->
<%= form_with model: @article do |f| %>
  <%= f.text_field :title %>
  <%= f.text_area :body %>
  <%= f.submit %>
<% end %>
```

## Turbo Frames

Turbo Frames enable scoped page updates:

```erb
<!-- app/views/articles/show.html.erb -->
<%= turbo_frame_tag "article_#{@article.id}" do %>
  <h1><%= @article.title %></h1>
  <p><%= @article.body %></p>
  <%= link_to "Edit", edit_article_path(@article) %>
<% end %>

<!-- app/views/articles/edit.html.erb -->
<%= turbo_frame_tag "article_#{@article.id}" do %>
  <%= form_with model: @article do |f| %>
    <%= f.text_field :title %>
    <%= f.text_area :body %>
    <%= f.submit %>
  <% end %>
<% end %>
```

Lazy loading with Turbo Frames:

```erb
<%= turbo_frame_tag "expensive_content", src: expensive_content_path, loading: :lazy %>
```

## Turbo Streams

Real-time updates with Turbo Streams:

```ruby
# app/controllers/comments_controller.rb
class CommentsController < ApplicationController
  def create
    @comment = @article.comments.create(comment_params)

    respond_to do |format|
      format.turbo_stream
      format.html { redirect_to @article }
    end
  end
end
```

```erb
<!-- app/views/comments/create.turbo_stream.erb -->
<%= turbo_stream.append "comments" do %>
  <%= render @comment %>
<% end %>

<%= turbo_stream.update "comment_form" do %>
  <%= render "comments/form", comment: Comment.new %>
<% end %>
```

Broadcasting with Action Cable:

```ruby
# app/models/comment.rb
class Comment < ApplicationRecord
  belongs_to :article

  after_create_commit -> { broadcast_append_to article, target: "comments" }
  after_update_commit -> { broadcast_replace_to article }
  after_destroy_commit -> { broadcast_remove_to article }
end
```

```erb
<!-- app/views/articles/show.html.erb -->
<%= turbo_stream_from @article %>

<div id="comments">
  <%= render @article.comments %>
</div>
```

## Stimulus Controllers

JavaScript sprinkles with Stimulus:

```javascript
// app/javascript/controllers/dropdown_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["menu"]

  toggle() {
    this.menuTarget.classList.toggle("hidden")
  }

  hide(event) {
    if (!this.element.contains(event.target)) {
      this.menuTarget.classList.add("hidden")
    }
  }
}
```

```erb
<!-- app/views/shared/_dropdown.html.erb -->
<div data-controller="dropdown" data-action="click@window->dropdown#hide">
  <button data-action="dropdown#toggle">Menu</button>
  <div data-dropdown-target="menu" class="hidden">
    <a href="#">Item 1</a>
    <a href="#">Item 2</a>
  </div>
</div>
```

## Form Validation with Stimulus

```javascript
// app/javascript/controllers/form_validator_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input", "error"]

  validate() {
    const value = this.inputTarget.value

    if (value.length < 3) {
      this.errorTarget.textContent = "Must be at least 3 characters"
      this.inputTarget.classList.add("border-red-500")
    } else {
      this.errorTarget.textContent = ""
      this.inputTarget.classList.remove("border-red-500")
    }
  }
}
```

## Turbo Stream Actions

Seven core actions:

```ruby
# append, prepend, replace, update, remove, before, after
turbo_stream.append "target_id", partial: "item", locals: { item: @item }
turbo_stream.prepend "target_id", html: content
turbo_stream.replace "target_id", @item
turbo_stream.update "target_id", html: "<p>Updated</p>"
turbo_stream.remove "target_id"
turbo_stream.before "target_id", partial: "item"
turbo_stream.after "target_id", partial: "item"
```

## Progressive Enhancement

Start with working HTML, enhance with Turbo:

```erb
<!-- Works without JavaScript -->
<%= form_with model: @article, url: articles_path do |f| %>
  <%= f.text_field :title %>
  <%= f.submit %>
<% end %>

<!-- Enhanced with Turbo Frame -->
<%= turbo_frame_tag "article_form" do %>
  <%= form_with model: @article do |f| %>
    <%= f.text_field :title %>
    <%= f.submit %>
  <% end %>
<% end %>
```

## Common Patterns

Inline editing:

```erb
<%= turbo_frame_tag dom_id(@article, :title) do %>
  <%= link_to @article.title, edit_article_path(@article),
              data: { turbo_frame: dom_id(@article, :title) } %>
<% end %>
```

Modal dialogs:

```erb
<%= turbo_frame_tag "modal" %>

<%= link_to "Open Modal", new_article_path,
            data: { turbo_frame: "modal" } %>
```

## Performance Tips

- Use lazy loading for off-screen frames
- Debounce Stimulus actions for search/autocomplete
- Cache Turbo Stream partials
- Use morphing for minimal DOM updates
- Minimize frame nesting depth
