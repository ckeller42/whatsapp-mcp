package main

import (
	"testing"

	waProto "go.mau.fi/whatsmeow/binary/proto"
	"google.golang.org/protobuf/proto"
)

func TestExtractTextContentPlainText(t *testing.T) {
	msg := &waProto.Message{Conversation: proto.String("hello")}
	if got := extractTextContent(msg); got != "hello" {
		t.Errorf("got %q, want %q", got, "hello")
	}
}

func TestExtractTextContentPoll(t *testing.T) {
	poll := &waProto.PollCreationMessage{
		Name: proto.String("Jahresauftakt-Treffen 2027, München"),
		Options: []*waProto.PollCreationMessage_Option{
			{OptionName: proto.String("16.1./17.1.2027")},
			{OptionName: proto.String("23.1./24.1.2027")},
		},
	}
	msg := &waProto.Message{PollCreationMessage: poll}

	want := "[Poll] Jahresauftakt-Treffen 2027, München\n- 16.1./17.1.2027\n- 23.1./24.1.2027"
	if got := extractTextContent(msg); got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}

func TestExtractTextContentPollV2AndV3(t *testing.T) {
	poll := &waProto.PollCreationMessage{
		Name:    proto.String("Q"),
		Options: []*waProto.PollCreationMessage_Option{{OptionName: proto.String("A")}},
	}

	v2 := &waProto.Message{PollCreationMessageV2: poll}
	if got := extractTextContent(v2); got != "[Poll] Q\n- A" {
		t.Errorf("V2: got %q", got)
	}

	v3 := &waProto.Message{PollCreationMessageV3: poll}
	if got := extractTextContent(v3); got != "[Poll] Q\n- A" {
		t.Errorf("V3: got %q", got)
	}
}

func TestExtractTextContentNilAndEmpty(t *testing.T) {
	if got := extractTextContent(nil); got != "" {
		t.Errorf("nil message: got %q, want empty", got)
	}
	if got := extractTextContent(&waProto.Message{}); got != "" {
		t.Errorf("empty message: got %q, want empty", got)
	}
}
