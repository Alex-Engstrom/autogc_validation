-- Removes the title, author, and date metadata blocks from docx output only.
if FORMAT:match('docx') then
  function Meta(meta)
    meta.title  = nil
    meta.author = nil
    meta.date   = nil
    return meta
  end
end
