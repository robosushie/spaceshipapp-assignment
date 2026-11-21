retry_policy Once {
  max_retries 1
  strategy {
    type constant_delay
    delay_ms 200
  }
}

client<llm> AnthropicSonnet {
  provider anthropic
  retry_policy Once
  options {
    model "claude-sonnet-5-5"
    api_key env.ANTHROPIC_API_KEY
  }
}
